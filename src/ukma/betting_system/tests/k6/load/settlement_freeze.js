import http from 'k6/http';
import { createUser, loggedParams } from '../common.js';

const BASE_URL = 'http://localhost:8080/api/v1';

export const options = {
    vus: 20,
    iterations: 5,
    thresholds: {
        http_req_duration: ['p(90)<2000'],
    },
};

//settlement is ongoing, db may be locked

export function setup() {
    return createUser(100);
}

export default function (token) {
    http.get(`${BASE_URL}/wallet/balance`, loggedParams(token));
}