# Security policy

## Supported versions

Security fixes are applied to the latest release only. The current line is **0.10.x**.

## Reporting a vulnerability

Please use **GitHub private vulnerability reporting**:

1. Open the **Security** tab of this repository.
2. Choose **Report a vulnerability**.
3. Describe the problem, the affected version and the smallest reproduction you can share.

Do **not** open a public issue for a security problem. Do not include credentials, Home Assistant tokens, personal archives or photos from a real collection in the report.

If private reporting is unavailable, contact the maintainer through the GitHub profile [@kriptos1970](https://github.com/kriptos1970).

## Scope

Examples of issues in scope:

- the Ingress boundary and authentication of the add-on;
- archive import, path traversal and file handling;
- photo upload, EXIF stripping and thumbnail generation;
- handling of provider keys and the Home Assistant Supervisor token;
- prompt construction and handling of AI responses;
- dependencies shipped with the add-on.

Out of scope: vulnerabilities in Home Assistant itself, third-party providers (Pl@ntNet, Perenual, Open Plantbook, iNaturalist, Gemini, OpenAI), or the user's network and hardware.

## Disclosure

Reports are acknowledged on a best-effort basis, usually within a few days. Please allow time for a fix before public disclosure. Credit is given in the release notes unless you prefer to stay anonymous.
