import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost";
const VUS = Number(__ENV.VUS || 10);
const DURATION = String(__ENV.DURATION || "30s");

export const options = {
  vus: VUS,
  duration: DURATION,
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1500"],
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/api/health`, { timeout: "5s" });
  check(res, { "health: 200": (r) => r.status === 200 });
  sleep(0.2);
}

