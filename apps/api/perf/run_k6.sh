#!/usr/bin/env bash

set -euo pipefail

default_base_url() {
  case "$(uname -s)" in
    Darwin)
      echo "http://host.docker.internal:8000"
      ;;
    *)
      echo "http://127.0.0.1:8000"
      ;;
  esac
}

BASE_URL="${BASE_URL:-$(default_base_url)}"

is_local_host() {
  case "$1" in
    127.0.0.1|localhost|0.0.0.0|::1|host.docker.internal)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

extract_hostname() {
  python - "$1" <<'PY'
import sys
from urllib.parse import urlparse

print(urlparse(sys.argv[1]).hostname or '')
PY
}

confirm_remote_target() {
  local url="$1"
  if [[ ! -t 0 ]]; then
    echo "Refusing to target non-local BASE_URL=$url without an interactive terminal." >&2
    exit 1
  fi

  echo "WARNING: non-local target detected: BASE_URL=$url" >&2
  read -r -p "Type 'yes' to continue: " confirmation
  if [[ "$confirmation" != "yes" ]]; then
    echo "Aborted by user." >&2
    exit 1
  fi
}

hostname="$(extract_hostname "$BASE_URL")"

if ! is_local_host "$hostname"; then
  confirm_remote_target "$BASE_URL"
fi

docker_args=(
  run
  --rm
  -i
  -v "$PWD:/work"
  -w /work
  -e "BASE_URL=$BASE_URL"
)

if [[ -n "${ENDPOINT:-}" ]]; then
  docker_args+=(-e "ENDPOINT=$ENDPOINT")
fi
if [[ -n "${METHOD:-}" ]]; then
  docker_args+=(-e "METHOD=$METHOD")
fi
if [[ -n "${AUTHORIZATION:-}" ]]; then
  docker_args+=(-e "AUTHORIZATION=$AUTHORIZATION")
fi
if [[ -n "${PAYLOAD:-}" ]]; then
  docker_args+=(-e "PAYLOAD=$PAYLOAD")
fi
if [[ -n "${RATE_STAGES:-}" ]]; then
  docker_args+=(-e "RATE_STAGES=$RATE_STAGES")
fi
if [[ -n "${TIME_UNIT:-}" ]]; then
  docker_args+=(-e "TIME_UNIT=$TIME_UNIT")
fi
if [[ -n "${PRE_ALLOCATED_VUS:-}" ]]; then
  docker_args+=(-e "PRE_ALLOCATED_VUS=$PRE_ALLOCATED_VUS")
fi
if [[ -n "${MAX_VUS:-}" ]]; then
  docker_args+=(-e "MAX_VUS=$MAX_VUS")
fi
if [[ -n "${SLEEP_SECONDS:-}" ]]; then
  docker_args+=(-e "SLEEP_SECONDS=$SLEEP_SECONDS")
fi
if [[ -n "${CAMPAIGN_ID:-}" ]]; then
  docker_args+=(-e "CAMPAIGN_ID=$CAMPAIGN_ID")
fi
if [[ -n "${PROCESS_QUERY:-}" ]]; then
  docker_args+=(-e "PROCESS_QUERY=$PROCESS_QUERY")
fi
if [[ -n "${EXPECTED_STATUSES:-}" ]]; then
  docker_args+=(-e "EXPECTED_STATUSES=$EXPECTED_STATUSES")
fi
if [[ -n "${EXPECTED_CONTENT_TYPE:-}" ]]; then
  docker_args+=(-e "EXPECTED_CONTENT_TYPE=$EXPECTED_CONTENT_TYPE")
fi
if [[ -n "${PROCESS_RATE_STAGES:-}" ]]; then
  docker_args+=(-e "PROCESS_RATE_STAGES=$PROCESS_RATE_STAGES")
fi
if [[ -n "${PROCESS_TIME_UNIT:-}" ]]; then
  docker_args+=(-e "PROCESS_TIME_UNIT=$PROCESS_TIME_UNIT")
fi
if [[ -n "${PROCESS_PRE_ALLOCATED_VUS:-}" ]]; then
  docker_args+=(-e "PROCESS_PRE_ALLOCATED_VUS=$PROCESS_PRE_ALLOCATED_VUS")
fi
if [[ -n "${PROCESS_MAX_VUS:-}" ]]; then
  docker_args+=(-e "PROCESS_MAX_VUS=$PROCESS_MAX_VUS")
fi
if [[ -n "${CLICK_RATE_STAGES:-}" ]]; then
  docker_args+=(-e "CLICK_RATE_STAGES=$CLICK_RATE_STAGES")
fi
if [[ -n "${CLICK_TIME_UNIT:-}" ]]; then
  docker_args+=(-e "CLICK_TIME_UNIT=$CLICK_TIME_UNIT")
fi
if [[ -n "${REPORT_RATE_STAGES:-}" ]]; then
  docker_args+=(-e "REPORT_RATE_STAGES=$REPORT_RATE_STAGES")
fi
if [[ -n "${REPORT_TIME_UNIT:-}" ]]; then
  docker_args+=(-e "REPORT_TIME_UNIT=$REPORT_TIME_UNIT")
fi
if [[ -n "${LEAD_PROBABILITY:-}" ]]; then
  docker_args+=(-e "LEAD_PROBABILITY=$LEAD_PROBABILITY")
fi
if [[ -n "${POSTBACK_PROBABILITY:-}" ]]; then
  docker_args+=(-e "POSTBACK_PROBABILITY=$POSTBACK_PROBABILITY")
fi
if [[ -n "${LEAD_DELAY_SECONDS:-}" ]]; then
  docker_args+=(-e "LEAD_DELAY_SECONDS=$LEAD_DELAY_SECONDS")
fi
if [[ -n "${POSTBACK_DELAY_SECONDS:-}" ]]; then
  docker_args+=(-e "POSTBACK_DELAY_SECONDS=$POSTBACK_DELAY_SECONDS")
fi
if [[ -n "${TRACK_PRE_ALLOCATED_VUS:-}" ]]; then
  docker_args+=(-e "TRACK_PRE_ALLOCATED_VUS=$TRACK_PRE_ALLOCATED_VUS")
fi
if [[ -n "${TRACK_MAX_VUS:-}" ]]; then
  docker_args+=(-e "TRACK_MAX_VUS=$TRACK_MAX_VUS")
fi
if [[ -n "${REPORT_PRE_ALLOCATED_VUS:-}" ]]; then
  docker_args+=(-e "REPORT_PRE_ALLOCATED_VUS=$REPORT_PRE_ALLOCATED_VUS")
fi
if [[ -n "${REPORT_MAX_VUS:-}" ]]; then
  docker_args+=(-e "REPORT_MAX_VUS=$REPORT_MAX_VUS")
fi
if [[ -n "${REPORTS_START_TIME:-}" ]]; then
  docker_args+=(-e "REPORTS_START_TIME=$REPORTS_START_TIME")
fi

case "$(uname -s)" in
  Linux)
    docker_args+=(--network host)
    ;;
esac

docker_args+=(grafana/k6 run "$@")

exec docker "${docker_args[@]}"
