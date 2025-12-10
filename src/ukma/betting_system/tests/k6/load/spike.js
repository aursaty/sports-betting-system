import http from 'k6/http';
import { check, sleep } from 'k6';
import { createUser, loggedParams } from '../common.js';

const BASE_URL = 'http://localhost:8080/api/v1';

export const options = {
    stages: [
      { duration: '1m', target: 50 },  
      { duration: '30s', target: 2000 }, 
      { duration: '5m', target: 2000 }, 
      { duration: '1m', target: 0 },    
    ],
  };

const EVENT_ID = '12345';

const tokens = [];

export function setup() {
    for (let i = 0; i < 2000; i++) {
        const token = createUser(100); 
        sleep(0.05);
        tokens.push(token);
    }
}

export default function () {
    const params = loggedParams(tokens[__VU - 1]);

    const depositRes = http.post(`${BASE_URL}/wallet/deposit`, JSON.stringify({ amount: 100 }), params);
    check(depositRes, {
        'deposit status is 200': (r) => r.status === 200,
    });

    const eventRes = http.get(`${BASE_URL}/events/${EVENT_ID}`, params);
    check(eventRes, {
        'event fetch status is 200': (r) => r.status === 200,
    });
    const eventOdds = eventRes.json('odds.0.value');

    const betRequest = JSON.stringify({
        eventId: EVENT_ID,
        amount: 100,
        outcome: Math.random() > 0.5 ? 0 : 1,
        odds: eventOdds - 0.4,
    });

    const betRes = http.post(`${BASE_URL}/bets`, betRequest, params);
    check(betRes, {
        'bet status is 200': (r) => r.status === 200
    });
}
