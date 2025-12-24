import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost";
const ADMIN_EMAIL = __ENV.ADMIN_EMAIL || "";
const ADMIN_PASSWORD = __ENV.ADMIN_PASSWORD || "";

export const options = {
  vus: 1,
  iterations: 1,
};

function randEmail() {
  const n = Math.floor(Math.random() * 1e9);
  return `k6_${n}@example.com`;
}

export default function () {
  const health = http.get(`${BASE_URL}/api/health`, { timeout: "5s" });
  check(health, {
    "health: 200": (r) => r.status === 200,
    "health: ok": (r) => r.json("ok") === true,
  });

  const email = randEmail();
  const password = "password123";
  const reg = http.post(
    `${BASE_URL}/api/auth/register`,
    JSON.stringify({ email, password }),
    { headers: { "Content-Type": "application/json" }, timeout: "10s" }
  );
  check(reg, { "register: 200": (r) => r.status === 200 });
  const token = reg.json("access_token");
  check(token, { "register: token exists": (t) => !!t });

  const me = http.get(`${BASE_URL}/api/users/me`, {
    headers: { Authorization: `Bearer ${token}` },
    timeout: "10s",
  });
  check(me, {
    "me: 200": (r) => r.status === 200,
    "me: email matches": (r) => r.json("email") === email,
  });

  if (ADMIN_EMAIL && ADMIN_PASSWORD) {
    const login = http.post(
      `${BASE_URL}/api/auth/login`,
      JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
      { headers: { "Content-Type": "application/json" }, timeout: "10s" }
    );
    check(login, { "admin login: 200": (r) => r.status === 200 });
    const adminToken = login.json("access_token");
    const metrics = http.get(`${BASE_URL}/api/admin/metrics`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      timeout: "10s",
    });
    check(metrics, { "admin metrics: 200": (r) => r.status === 200 });
  }

  sleep(0.2);
}

