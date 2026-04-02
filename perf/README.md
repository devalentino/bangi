Use `k6` to find the highest stable request rate under the current Docker memory limits.

Seed realistic historical data before running the benchmark:

```bash
export $(grep -v '^#' .env | xargs) && python perf/seed.py --campaign-id 1 --clicks 1000000 --lead-ratio 0.15 --postback-ratio 0.85 --days 14
```

Safety guard:

- `perf/seed.py` prompts for confirmation if `MARIADB_HOST` is non-local.
- `perf/run_k6.sh` prompts for confirmation if `BASE_URL` is non-local.
- You must type `yes` before the script proceeds.

Examples:

```bash
export $(grep -v '^#' .env | xargs) && python perf/seed.py --campaign-id 1 --clicks 1000000
```

```bash
BASE_URL=https://example.com bash perf/run_k6.sh perf/single_endpoint.js
```

If you want to replace existing tracker data for that campaign:

```bash
export $(grep -v '^#' .env | xargs) && python perf/seed.py --campaign-id 1 --clicks 1000000 --lead-ratio 0.15 --postback-ratio 0.85 --days 14 --truncate
```

Suggested flow:

1. Start the stack.
2. Start observers in one terminal.
3. Run `k6` in another terminal.
4. Review `docker stats`, compose logs, latency percentiles, and error rate.

Observer:

```bash
bash perf/observe.sh perf/out
```

Health endpoint example:

```bash
BASE_URL=http://host.docker.internal:8000 \
ENDPOINT=/api/v2/health \
RATE_STAGES=5:2m,10:5m,15:5m,20:5m,25:5m \
bash perf/run_k6.sh perf/single_endpoint.js
```

Authorized leads report example:

```bash
BASE_URL=http://host.docker.internal:8000 \
ENDPOINT='/api/v2/reports/leads?campaignId=1&page=1&pageSize=20&sortBy=createdAt&sortOrder=desc' \
AUTHORIZATION='Basic <base64-user-pass>' \
TIME_UNIT=1m \
RATE_STAGES=1:5m \
bash perf/run_k6.sh perf/single_endpoint.js
```

Authorized statistics report example:

```bash
BASE_URL=http://host.docker.internal:8000 \
ENDPOINT='/api/v2/reports/statistics?campaignId=1&periodStart=2026-03-23&periodEnd=2026-03-23' \
AUTHORIZATION='Basic <base64-user-pass>' \
TIME_UNIT=1m \
RATE_STAGES=1:5m \
bash perf/run_k6.sh perf/single_endpoint.js
```

POST example:

```bash
BASE_URL=http://host.docker.internal:8000 \
ENDPOINT=/api/v2/track/click \
METHOD=POST \
PAYLOAD='{"clickId":"550e8400-e29b-41d4-a716-446655440000","campaignId":1}' \
RATE_STAGES=5:2m,10:5m,15:5m \
bash perf/run_k6.sh perf/single_endpoint.js
```

For `perf/single_endpoint.js`, `RATE_STAGES` are interpreted relative to `TIME_UNIT`. For example, `TIME_UNIT=1m` with `RATE_STAGES=1:5m` means 1 request per minute for 5 minutes.

What to look for:

- Stable rate: no restarts, no OOM, error rate under 1%, p95 acceptable.
- Degradation point: p95/p99 jumps sharply or swap/CPU stays pinned.
- Failure point: healthcheck failures, container restarts, OOM kills, or sustained 5xx/timeouts.

Useful host-side commands during the run:

```bash
docker compose ps
docker compose top
free -m
vmstat 1
```

Mixed workload example:

This runs click registration continuously, sometimes creates leads/postbacks for the same click, and hits report endpoints in parallel.

```bash
BASE_URL=http://host.docker.internal:8000 \
CAMPAIGN_ID=1 \
AUTHORIZATION='Basic <base64-user-pass>' \
CLICK_RATE_STAGES=5:2m,10:5m,15:5m,20:5m \
CLICK_TIME_UNIT=1s \
REPORT_RATE_STAGES=1:2m,2:5m,3:5m \
REPORT_TIME_UNIT=1m \
LEAD_PROBABILITY=0.30 \
POSTBACK_PROBABILITY=0.15 \
LEAD_DELAY_SECONDS=10 \
POSTBACK_DELAY_SECONDS=15 \
bash perf/run_k6.sh perf/mixed_workload.js
```

How the mixed scenario works:

- Every tracking iteration sends one `/api/v2/track/click`.
- About `30%` of clicks also send `/api/v2/track/lead` after `10s`.
- About `15%` of leads also send `/api/v2/track/postback` after another `15s`.
- `CLICK_RATE_STAGES` and `REPORT_RATE_STAGES` are interpreted relative to `CLICK_TIME_UNIT` and `REPORT_TIME_UNIT`.
- A parallel scenario reads:
  - `/api/v2/reports/leads`
  - `/api/v2/reports/statistics`

Recommended process:

1. Seed one realistic campaign with enough historical clicks.
2. Start `perf/observe.sh`.
3. Run `perf/mixed_workload.js` with low stages first.
4. Increase click rate until you see either:
   - `p95/p99` jump sharply
   - `5xx` or timeouts
   - backend or MariaDB restarts
   - swap growth that does not recover

Suggested first target on a 512 MB host:

- clicks: `5 -> 10 -> 15 -> 20 rps`
- reports: `1 -> 2 -> 3 rps`

Then raise one side at a time:

- If writes are stable, increase reports.
- If reports are stable, increase clicks.
- Once one component starts degrading, you found the likely bottleneck.
