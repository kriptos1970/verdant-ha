# Archive scale (unreleased)

Plant documents in SQLite remain the source of truth. The general care-history endpoint now uses a derived SQLite table with one row per non-deleted care event. The table holds filter and sorting keys and the event's position in its plant document, not a second copy of the event body. Only the requested page loads event bodies.

- An existing database is indexed on first start, in one transaction. SQLite triggers keep the index in sync with the source documents on writes, permanent deletes and in-place restore. The existing rules for filters, local dates and pagination still apply.
- ZIP/JSON backups, API responses and photo handling are unchanged. The web backup stores the source documents, not the derived index. A restore repopulates the index as it writes the documents.
- The trade-off is more SQLite disk space and write work when a plant's history or room changes. This does not speed up collection summaries or analytics; those still read the full plant documents.

## Repeat the benchmark

```sh
.venv/bin/python scripts/benchmark_archive.py --plants 400 --events 500 --skip-full
.venv/bin/python scripts/benchmark_archive.py --plants 500 --events 1000 --skip-full
```

The script uses a fresh temporary database and no real photos, Home Assistant calls or scheduler. After one warm-up, it reports the median, p95 and response size for 20 sequential in-process API requests per view. Prefix the command with `/usr/bin/time -l` on macOS (or `/usr/bin/time -v` on Linux) for peak process RSS. That number includes seeding, Python and the test client; it is not the RAM needed by Verdant on Home Assistant. Omit `--skip-full` to include the unpaginated legacy response for a separate size comparison.

## Development Mac results

Same workload before and after, with 400 plants and 200,000 events. Times are API milliseconds; network/Ingress and browser rendering are excluded.

| View | Median before → after | p95 before → after |
|---|---:|---:|
| Care history, first 50 events | 697.3 → 28.6 | 706.0 → 32.5 |
| Care history, room + kind + last 30 days | 482.9 → 22.3 | 487.7 → 24.5 |
| Collection summary | 937.1 → 1,051.9 | 1,106.1 → 1,253.9 |
| Plant detail | 6.3 → 8.9 | 7.0 → 10.8 |
| Analytics, 30 days | 321.4 → 352.6 | 356.6 → 443.1 |

The indexed database grew from **51.1 MB to 116.5 MB**. Seeding the same archive took 0.58 s before and 4.83 s after; that bulk-write test is not a measurement of individual care edits. Peak RSS for the complete benchmark, excluding the unpaginated response, was about **248 MB before and 243 MB after**. The history responses were still about 18.5 kB. The other views were not optimized; the next place to investigate, if needed on hardware, is the collection summary. These measurements did not go through Home Assistant.

With the index at **500 plants and 500,000 events**, p95 was **46.5 ms** for the first history page, **35.8 ms** with the filters above and **2.12 s** for the collection summary. The temporary database was 292 MB and peak process RSS was 507 MB, excluding the unpaginated endpoint.

## Home Assistant OS rehearsal (Mac VM)

The isolated ARM64 VM ran Home Assistant OS 18.4 with two vCPUs and 3.5 GiB of RAM. The comparison uses published Verdant 1.0.3 and a local build of the same image with only the history-index backend files replaced. Both imported the same synthetic ZIP; measurements are 20 sequential HTTP requests per view after one warm-up through Home Assistant Ingress. They include request and response transfer on the Mac loopback interface, not browser rendering. No photos or personal data were used, and nothing ran on the production Home Assistant host.

For **400 plants and 200,000 events**:

| View | p95, Verdant 1.0.3 | p95, with index |
|---|---:|---:|
| First history page | 797.5 ms | 25.6 ms |
| History filtered by room, kind and date | 501.4 ms | 21.3 ms |
| Collection summary | 729.4 ms | 772.9 ms |
| Plant detail | 8.9 ms | 10.2 ms |
| Analytics, 30 days | 323.6 ms | 323.5 ms |

Counts, filtered totals and two non-overlapping 50-row pages were verified in both builds. The ZIP import into an empty archive took 1.42 s before and 5.31 s after; the reported SQLite size went from 51.1 MB to 116.5 MB.

With **500 plants and 500,000 events** and shorter notes, the indexed build imported the ZIP over the 200,000-event archive in **15.9 s**. The p95 was **62.2 ms** for the first history page, **49 ms** with filters, **25 ms** for a plant detail, **870.2 ms** for 30-day analytics and **2.19 s** for the collection summary. Chromium opened the collection, plant detail and diary and displayed a filtered 50-row history page with an API total of 1,000 events for the selected plant.

**Import limit found:** a second 500,000-event ZIP with longer notes had a valid checksum and a `data.json` of 121,767,447 bytes, below the 150 MiB ZIP metadata limit. Preview returned HTTP 422 because ZIP decoding wraps that JSON in base64 before applying the JSON envelope limit; the base64 representation alone is over 150 MiB. The 97,767,447-byte version with shorter notes passed. This is an import-size issue, not a limit on the number of stored events.
