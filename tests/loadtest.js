import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 50 },   // ramp up to 50 users
    { duration: '1m', target: 50 },    // hold at 50 users
    { duration: '10s', target: 0 },    // ramp down
  ],
};

export default function () {
  let res = http.get('http://47.84.47.124/');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1); // simulate user think time
}
