Use `k6` to find the highest stable request rate for regular user behavior:

- tracking writes plus report reads;
- campaign process traffic plus report reads.

## Runtime Model

Use semantic origins instead of environment-specific names:

- `DASHBOARD_BASE_URL`: dashboard/API origin. Used for `/api/v2/track/*` and `/api/v2/reports/*`.
- `CAMPAIGN_BASE_URL`: campaign entrypoint. Required for every run. Used by the process workload; kept in track workload run metadata for consistency.
- `CAMPAIGN_ID`: existing campaign id used by reports and local direct process URLs.

`perf/run_k6.sh` prompts before targeting non-local dashboard or campaign origins. Run external tests from an interactive terminal and type `yes` to continue.
`CAMPAIGN_BASE_URL` is required for both workloads; the wrapper refuses to run without it.

Local Docker Compose usually uses the backend directly:

```bash
DASHBOARD_BASE_URL=http://host.docker.internal:8000
CAMPAIGN_BASE_URL=http://host.docker.internal:8000/process/1
```

External nginx-managed environments use separate public origins:

```bash
DASHBOARD_BASE_URL=https://dashboard.example.com
CAMPAIGN_BASE_URL=https://campaign.example.com
```

Do not run process traffic against `https://dashboard.example.com/process/<campaignId>` externally. Dashboard nginx configs return `404` for `/process`. Campaign domains proxy their root path to the backend process route.

## Setup Paths
Choose one setup path before running a workload.

| Target | Configuration source | Historical data | Observability |
| --- | --- | --- | --- |
| Local Docker Compose | Manually through dashboard/API | Seed scripts | Local Docker artifacts plus k6 artifacts |
| External host | Manually through dashboard/API | Seed scripts through exposed MariaDB | External server, nginx, app, and DB metrics plus k6 artifacts |

Seed scripts are used to fill historical tracker data for realistic report reads. Current seed scripts also create campaign fixtures and require an empty `campaign` table, so they fit fresh performance databases. They do not create domains, nginx configs, or certificates. `KAN-74` tracks the follow-up to seed history for an already configured campaign.

## Manual Environment Setup

Create the performance target through the product path so nginx and certificates are exercised the same way as real usage.

Required for both workloads:

1. Create or choose a campaign.
2. Note the campaign id as `CAMPAIGN_ID`.
3. Configure dashboard/API access and prepare the `AUTHORIZATION` header for report endpoints.
4. Confirm `DASHBOARD_BASE_URL/api/v2/reports/statistics` and `DASHBOARD_BASE_URL/api/v2/reports/leads` are reachable with that auth.

Create the Basic auth value on Linux:

```bash
printf 'admin:<password>' | base64 -w 0; echo
```

Use it as:

```bash
AUTHORIZATION='Basic <base64-user-pass>'
```

Additional requirements for the track workload:

1. Confirm `DASHBOARD_BASE_URL/api/v2/track/click` accepts events for the campaign.
2. Set `CAMPAIGN_BASE_URL` to the campaign entrypoint for consistency, even though this workload does not send traffic there.

Additional requirements for the process workload:

1. Create an enabled flow for the campaign.
2. Create and enable a campaign domain for the campaign.
3. Wait until nginx generation and certificate issuance are complete.
4. Confirm the campaign domain root responds as expected:
   - redirect flow: `302`;
   - render flow: `200` with the expected content type.
5. Use the campaign domain root as `CAMPAIGN_BASE_URL`.

## Historical Data

Historical rows make report reads more realistic. Current seed scripts fill historical tracker rows and also create the required campaign fixtures. They require an empty `campaign` table.

Pass DB connection settings explicitly when running seed scripts:

```bash
MARIADB_HOST=127.0.0.1 \
MARIADB_PORT=3306 \
MARIADB_USER=bangi \
MARIADB_PASSWORD='<password>' \
MARIADB_DATABASE=bangi \
python perf/track_and_reports_seed.py --clicks 1000000 --lead-ratio 0.15 --postback-ratio 0.85 --days 14
```

```bash
MARIADB_HOST=127.0.0.1 \
MARIADB_PORT=3306 \
MARIADB_USER=bangi \
MARIADB_PASSWORD='<password>' \
MARIADB_DATABASE=bangi \
python perf/process_and_reports_seed.py --action-type redirect --clicks 1000000 --lead-ratio 0.30 --postback-ratio 0.85 --days 14
```

For external hosts, expose MariaDB only in a controlled performance environment. The seed scripts prompt when `MARIADB_HOST` is non-local and refuse to run without an interactive confirmation.

Do not run current seed scripts against an environment with existing campaigns. Use a fresh performance database, then complete any required dashboard domain and campaign domain setup through the product path.

## Artifact Collection

Create a run directory and write all artifacts there. Analyze artifacts after the run instead of relying on live observation.

```bash
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-track"
OUT_DIR="perf/out/$RUN_ID"
mkdir -p "$OUT_DIR"
```

For local Docker Compose, start the observer in a separate terminal before k6. It records Docker stats, container health snapshots, and compose logs into `OUT_DIR` for post-run analysis:

```bash
bash perf/observe.sh "$OUT_DIR"
```

Run k6 with a JSON summary:

```bash
bash perf/run_k6.sh --summary-export "$OUT_DIR/k6-summary.json" perf/<workload>.js 2>&1 | tee "$OUT_DIR/k6-output.log"
```

For external runs, export matching metrics for the same time window into the same run directory when possible:

- application CPU, memory, restarts, and 5xx rate;
- nginx access/error rates;
- MariaDB CPU, memory, connections, slow queries, and lock waits;
- host CPU, memory, disk IO, and network IO.

Keep screenshots, CSV exports, or links to dashboards in the run directory or in a short `external-metrics.md` file next to `k6-summary.json`.

## Track And Reports

This workload writes tracking events and reads report endpoints in parallel.

Behavior:

- `/api/v2/track/click` for every tracking iteration;
- `/api/v2/track/lead` for a configurable subset of clicks;
- `/api/v2/track/postback` for a configurable subset of leads;
- `/api/v2/reports/leads` and `/api/v2/reports/statistics` in a parallel scenario.

Local example:

```bash
DASHBOARD_BASE_URL=http://host.docker.internal:8000 \
CAMPAIGN_BASE_URL=http://host.docker.internal:8000/process/1 \
CAMPAIGN_ID=1 \
AUTHORIZATION='Basic YWRtaW46YWRtaW4K' \
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

External example:

```bash
DASHBOARD_BASE_URL=https://dashboard.example.com \
CAMPAIGN_BASE_URL=https://campaign.example.com \
CAMPAIGN_ID=123 \
AUTHORIZATION='Basic <base64-user-pass>' \
CLICK_RATE_STAGES=2:2m,5:5m,10:5m \
CLICK_TIME_UNIT=1s \
REPORT_RATE_STAGES=1:2m,2:5m \
REPORT_TIME_UNIT=1m \
LEAD_PROBABILITY=0.30 \
POSTBACK_PROBABILITY=0.85 \
LEAD_DELAY_SECONDS=10 \
POSTBACK_DELAY_SECONDS=15 \
bash perf/run_k6.sh perf/track_and_reports_workload.js
```

## Process And Reports

This workload sends campaign process traffic and reads report endpoints in parallel.

Behavior:

- process traffic goes to `CAMPAIGN_BASE_URL`;
- postbacks go to `DASHBOARD_BASE_URL/api/v2/track/postback`;
- reports go to `DASHBOARD_BASE_URL/api/v2/reports/*`;
- redirects are not followed, so redirect flows measure the gateway response.
- cookies are cleared before every process iteration, so each process request behaves like a fresh visitor and does not reuse flow cookies.

Local redirect-flow example:

```bash
DASHBOARD_BASE_URL=http://host.docker.internal:8000 \
CAMPAIGN_BASE_URL=http://host.docker.internal:8000/process/1 \
CAMPAIGN_ID=1 \
AUTHORIZATION='Basic YWRtaW46YWRtaW4K' \
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

External redirect-flow example:

```bash
DASHBOARD_BASE_URL=https://dashboard.example.com \
CAMPAIGN_BASE_URL=https://campaign.example.com \
CAMPAIGN_ID=123 \
AUTHORIZATION='Basic <base64-user-pass>' \
PROCESS_QUERY='{"status":"accept","tid":"123","payout":10,"offer_id":"456","lead_status":"accept,expect","sale_status":"confirm","rejected_status":"reject,fail,trash,error","return":"OK","from":"terraleads.com"}' \
EXPECTED_STATUSES=302 \
PROCESS_RATE_STAGES=2:2m,5:5m,10:5m \
PROCESS_TIME_UNIT=1s \
REPORT_RATE_STAGES=1:2m,2:5m \
REPORT_TIME_UNIT=1m \
POSTBACK_PROBABILITY=0.15 \
POSTBACK_DELAY_SECONDS=15 \
bash perf/run_k6.sh perf/process_and_reports_workload.js
```

Render flows use the same shape with:

```bash
EXPECTED_STATUSES=200
EXPECTED_CONTENT_TYPE='text/html; charset=utf-8'
```

## Reading Results

Stable rate:

- no restarts or OOM kills;
- k6 `http_req_failed` below threshold;
- checks above threshold;
- p95/p99 stay within the workload target;
- server and database metrics do not stay pinned.

Degradation point:

- p95/p99 jump sharply;
- 5xx or timeout rate increases;
- DB lock waits, slow queries, or connection pressure appear;
- CPU, memory, or IO saturates for sustained periods.

Failure point:

- health checks fail;
- containers restart;
- nginx returns sustained 5xx;
- MariaDB exhausts connections or stalls;
- k6 cannot maintain the requested arrival rate.
