import http from 'k6/http';
import { check } from 'k6';
import { createUser, loggedParams } from '../common.js';

const BASE_URL = 'http://localhost:8080/api/v1'; 

export const options = {
    scenarios: {
        double_spend_attack: {
            executor: 'per-vu-iterations',
            vus: 15,              
            iterations: 3,    
            duration: '20s',
        },
    },
};

export default function() {
    const token = createUser(100);

    const events = http.get(`${BASE_URL}/events?page=1&limit=1`, params);
    const eventId = events.json('events.0.id'); 

    const params = loggedParams(token);

    const betRequest = JSON.stringify({
        eventId: eventId,
        amount: 100, 
        outcome: 0,
    });

    const responses = http.batch([
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
    ]);

    check(responses, {
        'At most one bet succeeded': (resps) => resps.filter(r => r.status === 201).length <= 1,
    });

    const balanceRes = http.get(`${BASE_URL}/wallet/balance`, params);
    const finalBalance = balanceRes.json('balance');

    check(finalBalance, {
        'Balance is not negative': (balance) => balance >= 0,
        'Balance is exactly zero': (balance) => balance === 0,
    });
}