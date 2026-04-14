import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const campaignId = Number(__ENV.CAMPAIGN_ID || 1);
const authHeader = __ENV.AUTHORIZATION || '';
const leadDelaySeconds = Number(__ENV.LEAD_DELAY_SECONDS || 10);
const postbackDelaySeconds = Number(__ENV.POSTBACK_DELAY_SECONDS || 15);
const clickTimeUnit = __ENV.CLICK_TIME_UNIT || '1s';
const reportTimeUnit = __ENV.REPORT_TIME_UNIT || '1s';

const clickStages = (__ENV.CLICK_RATE_STAGES || '5:2m,10:5m,15:5m')
    .split(',')
    .filter(Boolean)
    .map((stage) => {
        const [target, duration] = stage.split(':');
        return { target: Number(target), duration };
    });

const reportStages = (__ENV.REPORT_RATE_STAGES || '1:2m,2:5m,3:5m')
    .split(',')
    .filter(Boolean)
    .map((stage) => {
        const [target, duration] = stage.split(':');
        return { target: Number(target), duration };
    });

const leadProbability = Number(__ENV.LEAD_PROBABILITY || 0.3);
const postbackProbability = Number(__ENV.POSTBACK_PROBABILITY || 0.15);

export const options = {
    discardResponseBodies: true,
    thresholds: {
        http_req_failed: ['rate<0.02'],
        http_req_duration: ['p(95)<1500', 'p(99)<3000'],
        checks: ['rate>0.98'],
    },
    scenarios: {
        track_flow: {
            executor: 'ramping-arrival-rate',
            exec: 'trackFlow',
            startRate: 1,
            timeUnit: clickTimeUnit,
            preAllocatedVUs: Number(__ENV.TRACK_PRE_ALLOCATED_VUS || 20),
            maxVUs: Number(__ENV.TRACK_MAX_VUS || 200),
            stages: clickStages,
        },
        reports_read: {
            executor: 'ramping-arrival-rate',
            exec: 'reportsRead',
            startRate: 1,
            timeUnit: reportTimeUnit,
            preAllocatedVUs: Number(__ENV.REPORT_PRE_ALLOCATED_VUS || 5),
            maxVUs: Number(__ENV.REPORT_MAX_VUS || 50),
            stages: reportStages,
            startTime: __ENV.REPORTS_START_TIME || '30s',
        },
    },
    summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

function uuid4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

export function trackFlow() {
    const clickId = uuid4();

    const clickResponse = http.post(
        `${baseUrl}/api/v2/track/click`,
        JSON.stringify({
            clickId,
            campaignId,
            source: 'k6',
            adset_name: `set-${__VU % 10}`,
            ad_name: `ad-${__ITER % 50}`,
            pixel: 'perf',
        }),
        {
            headers: { 'Content-Type': 'application/json' },
            tags: { endpoint: 'track_click' },
        }
    );

    check(clickResponse, {
        'track click status is 201': (r) => r.status === 201,
    });

    const hasLead = Math.random() < leadProbability;
    if (hasLead) {
        sleep(leadDelaySeconds);

        const leadResponse = http.post(
            `${baseUrl}/api/v2/track/lead`,
            JSON.stringify({
                clickId,
                state: 'queued',
                source: 'k6',
            }),
            {
                headers: { 'Content-Type': 'application/json' },
                tags: { endpoint: 'track_lead' },
            }
        );

        check(leadResponse, {
            'track lead status is 201': (r) => r.status === 201,
        });
    }

    if (hasLead && Math.random() < postbackProbability) {
        sleep(postbackDelaySeconds);

        const postbackResponse = http.post(
            `${baseUrl}/api/v2/track/postback`,
            JSON.stringify({
                clickId,
                state: 'executed',
                source: 'k6',
            }),
            {
                headers: { 'Content-Type': 'application/json' },
                tags: { endpoint: 'track_postback' },
            }
        );

        check(postbackResponse, {
            'track postback status is 201': (r) => r.status === 201,
        });
    }
}

export function reportsRead() {
    const headers = {};
    if (authHeader) {
        headers.Authorization = authHeader;
    }

    const leadsResponse = http.get(
        `${baseUrl}/api/v2/reports/leads?campaignId=${campaignId}&page=1&pageSize=20&sortBy=createdAt&sortOrder=desc`,
        {
            headers,
            tags: { endpoint: 'reports_leads' },
        }
    );
    check(leadsResponse, {
        'reports leads status is 200': (r) => r.status === 200,
    });

    const today = new Date().toISOString().slice(0, 10);
    const statisticsResponse = http.get(
        `${baseUrl}/api/v2/reports/statistics?campaignId=${campaignId}&periodStart=${today}&periodEnd=${today}`,
        {
            headers,
            tags: { endpoint: 'reports_statistics' },
        }
    );
    check(statisticsResponse, {
        'reports statistics status is 200': (r) => r.status === 200,
    });
}
