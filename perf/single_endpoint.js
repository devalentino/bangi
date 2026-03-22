import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const endpoint = __ENV.ENDPOINT || '/api/v2/health';
const method = (__ENV.METHOD || 'GET').toUpperCase();
const authHeader = __ENV.AUTHORIZATION || '';
const payload = __ENV.PAYLOAD || '';

const rateStages = (__ENV.RATE_STAGES || '5:2m,10:5m,15:5m,20:5m,25:5m')
    .split(',')
    .filter(Boolean)
    .map((stage) => {
        const [target, duration] = stage.split(':');
        return { target: Number(target), duration };
    });

const thresholds = {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000', 'p(99)<2500'],
    checks: ['rate>0.99'],
};

export const options = {
    discardResponseBodies: true,
    thresholds,
    scenarios: {
        sustained_rps: {
            executor: 'ramping-arrival-rate',
            startRate: 1,
            timeUnit: '1s',
            preAllocatedVUs: Number(__ENV.PRE_ALLOCATED_VUS || 20),
            maxVUs: Number(__ENV.MAX_VUS || 200),
            stages: rateStages,
        },
    },
    summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

function requestParams() {
    const headers = {};
    if (authHeader) {
        headers.Authorization = authHeader;
    }
    if (payload) {
        headers['Content-Type'] = 'application/json';
    }
    return { headers, tags: { endpoint, method } };
}

export default function () {
    const url = `${baseUrl}${endpoint}`;
    const params = requestParams();

    let response;
    if (method === 'POST') {
        response = http.post(url, payload, params);
    } else if (method === 'PATCH') {
        response = http.patch(url, payload, params);
    } else {
        response = http.get(url, params);
    }

    check(response, {
        'status is < 500': (r) => r.status < 500,
    });

    sleep(Number(__ENV.SLEEP_SECONDS || 0));
}
