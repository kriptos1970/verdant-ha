"""Verify that a GitHub Release exists for a tag and carries its assets.

The release workflow runs on every `v*` tag, so after pushing the tag this
script waits for the publication instead of assuming that `gh` or a token is
required. No credentials are needed for this public repository.
"""
import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.request

try:
    import certifi
except ImportError:  # pragma: no cover - CI and most Linux images have system CA files
    certifi = None

DEFAULT_REPO = "kriptos1970/verdant-ha"


def fetch(repo, tag, token=""):
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "verdant-release-check",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    context = ssl.create_default_context(cafile=certifi.where() if certifi else None)
    with urllib.request.urlopen(request, timeout=30, context=context) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="tag to verify, for example v0.11.22")
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"GitHub repository (default {DEFAULT_REPO})")
    parser.add_argument("--wait", type=int, default=90, help="seconds to keep retrying while the workflow runs (default 90)")
    parser.add_argument("--token", default="", help="optional token, only to avoid anonymous rate limits")
    args = parser.parse_args()

    if not args.tag.startswith("v"):
        parser.error("the tag must start with 'v', for example v0.11.22")

    deadline = time.monotonic() + max(0, args.wait)
    attempt = 0
    while True:
        attempt += 1
        try:
            release = fetch(args.repo, args.tag, args.token)
            break
        except urllib.error.HTTPError as error:
            if error.code != 404:
                print(f"GitHub API error {error.code} for {args.tag}", file=sys.stderr)
                return 2
            if time.monotonic() >= deadline:
                print(
                    f"Release {args.tag} is not published yet. "
                    "The Release workflow may still be running: check the Actions tab.",
                    file=sys.stderr,
                )
                return 1
            print(f"Release {args.tag} not found yet (attempt {attempt}); waiting for the workflow...")
            time.sleep(10)
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"Cannot reach the GitHub API: {error}", file=sys.stderr)
            return 2

    assets = release.get("assets") or []
    print(f"Release {args.tag}: draft={release.get('draft')} published={release.get('published_at')}")
    for asset in assets:
        print(f"  {asset.get('name')}  {asset.get('size')} bytes")
    if release.get("draft"):
        print(f"Release {args.tag} is still a draft.", file=sys.stderr)
        return 1
    if not any(str(asset.get("name", "")).endswith(".zip") for asset in assets):
        print(f"Release {args.tag} has no ZIP asset.", file=sys.stderr)
        return 1
    if not any(str(asset.get("name", "")).endswith(".sha256") for asset in assets):
        print(f"Release {args.tag} has no SHA256 asset.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
