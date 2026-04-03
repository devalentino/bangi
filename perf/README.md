Use `k6` to find the highest stable request rate under the current Docker memory limits.

## Common notes

Safety guard:

- `perf/track_and_reports_seed.py` prompts for confirmation if `MARIADB_HOST` is non-local.
- `perf/process_and_reports_seed.py` prompts for confirmation if `MARIADB_HOST` is non-local.
- `perf/process_and_reports_seed.py` also refuses to run if the `campaign` table is not empty.
- `perf/track_and_reports_seed.py` also refuses to run if the `campaign` table is not empty.
- `perf/run_k6.sh` prompts for confirmation if `BASE_URL` is non-local.
- You must type `yes` before the script proceeds.

Suggested flow:

1. Start the stack.
2. Start observers in one terminal.
3. Run `k6` in another terminal.
4. Review `docker stats`, compose logs, latency percentiles, and error rate.

Observer:

```bash
bash perf/observe.sh perf/out
```

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

## Track Performance Scenario

This workload continuously writes tracking data and reads both reports endpoints in parallel.

How it works:

- Every tracking iteration sends one `/api/v2/track/click`.
- About `30%` of clicks also send `/api/v2/track/lead` after `10s`.
- About `15%` of leads also send `/api/v2/track/postback` after another `15s`.
- A parallel scenario reads `/api/v2/reports/leads` and `/api/v2/reports/statistics`.
- `CLICK_RATE_STAGES` and `REPORT_RATE_STAGES` are interpreted relative to `CLICK_TIME_UNIT` and `REPORT_TIME_UNIT`.

Preparation:

Create a dedicated campaign and seed realistic historical data before running this workload:

```bash
export $(grep -v '^#' .env | xargs) && python perf/track_and_reports_seed.py --clicks 1000000 --lead-ratio 0.15 --postback-ratio 0.85 --days 14
```

The script only runs when the `campaign` table is empty, uses hardcoded perf campaign defaults, seeds tracker history, and prints the created `campaign_id`.
It also prints the final inserted `clicks`, `leads`, and `postbacks` counts.

Run:

```bash
BASE_URL=http://host.docker.internal:8000 \
CAMPAIGN_ID=<campaign-id-from-seed> \
AUTHORIZATION='Basic <base64-user-pass>' \
CLICK_RATE_STAGES=5:2m,10:5m,15:5m,20:5m \
CLICK_TIME_UNIT=1s \
REPORT_RATE_STAGES=1:2m,2:5m,3:5m \
REPORT_TIME_UNIT=1m \
LEAD_PROBABILITY=0.30 \
POSTBACK_PROBABILITY=0.85 \
LEAD_DELAY_SECONDS=10 \
POSTBACK_DELAY_SECONDS=15 \
bash perf/run_k6.sh perf/track_and_reports_workload.js
```

Suggested first target on a 512 MB host:

- clicks: `5 -> 10 -> 15 -> 20 rps`
- reports: `1 -> 2 -> 3 rps`

Then raise one side at a time:

- If writes are stable, increase reports.
- If reports are stable, increase clicks.
- Once one component starts degrading, you found the likely bottleneck.

## Process Performance Scenario

This workload continuously hits `/process/<campaignId>` and reads both reports endpoints in parallel.

How it works:

- Every process iteration sends one `GET /process/<campaignId>`.
- Each `/process` request gets a unique `clickId`.
- About `15%` of process clicks also send `/api/v2/track/postback` after `15s`.
- Redirects are not followed, so you measure the gateway response rather than the downstream landing target.
- A parallel scenario reads `/api/v2/reports/leads` and `/api/v2/reports/statistics`.
- `PROCESS_RATE_STAGES` and `REPORT_RATE_STAGES` are interpreted relative to `PROCESS_TIME_UNIT` and `REPORT_TIME_UNIT`.
- `POSTBACK_PROBABILITY` and `POSTBACK_DELAY_SECONDS` control the postback side flow.

Preparation:

- Create a dedicated campaign and flow for this scenario:
- The script only runs when the `campaign` table is empty.
- Campaign, flow, redirect URL, landing content, and campaign pricing use hardcoded perf defaults.
- The script also seeds tracker history for the created campaign before printing the result.

```bash
export $(grep -v '^#' .env | xargs) && python perf/process_and_reports_seed.py --action-type redirect --clicks 100000 --lead-ratio 0.30 --postback-ratio 0.15 --days 14
```

- For a render flow, create the campaign, flow, and landing files:

```bash
export $(grep -v '^#' .env | xargs) && python perf/process_and_reports_seed.py --action-type render --clicks 100000 --lead-ratio 0.30 --postback-ratio 0.15 --days 14
```

- The script prints the created `campaign_id`, `flow_id`, and `landing_index_path` for render flows.
- It also prints the final inserted `clicks`, `leads`, and `postbacks` counts.
- `LANDING_PAGES_BASE_PATH` must be set for `--action-type render`.

Run for redirect flows:

```bash
BASE_URL=http://host.docker.internal:8000 \
CAMPAIGN_ID=<campaign-id-from-seed> \
AUTHORIZATION='Basic <base64-user-pass>' \
PROCESS_QUERY='{"status":"accept","tid":"123","payout":10,"offer_id":"456","lead_status":"accept,expect","sale_status":"confirm","rejected_status":"reject,fail,trash,error","return":"OK","from":"terraleads.com"}' \
EXPECTED_STATUSES=302 \
PROCESS_RATE_STAGES=5:2m,10:5m,15:5m,20:5m \
PROCESS_TIME_UNIT=1s \
REPORT_RATE_STAGES=1:2m,2:5m,3:5m \
REPORT_TIME_UNIT=1m \
POSTBACK_PROBABILITY=0.15 \
POSTBACK_DELAY_SECONDS=15 \
bash perf/run_k6.sh perf/process_and_reports_workload.js
```

Run for render flows:

```bash
BASE_URL=http://host.docker.internal:8000 \
CAMPAIGN_ID=<campaign-id-from-seed> \
AUTHORIZATION='Basic <base64-user-pass>' \
PROCESS_QUERY='{"status":"accept","tid":"123","payout":10,"offer_id":"456","lead_status":"accept,expect","sale_status":"confirm","rejected_status":"reject,fail,trash,error","return":"OK","from":"terraleads.com"}' \
EXPECTED_STATUSES=200 \
EXPECTED_CONTENT_TYPE='text/html; charset=utf-8' \
PROCESS_RATE_STAGES=5:2m,10:5m,15:5m,20:5m \
PROCESS_TIME_UNIT=1s \
REPORT_RATE_STAGES=1:2m,2:5m,3:5m \
REPORT_TIME_UNIT=1m \
POSTBACK_PROBABILITY=0.15 \
POSTBACK_DELAY_SECONDS=15 \
bash perf/run_k6.sh perf/process_and_reports_workload.js
```
