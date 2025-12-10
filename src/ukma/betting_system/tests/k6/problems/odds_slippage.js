import http from 'k6/http';
import { check } from 'k6';
import { createUser, loggedParams } from '../common.js';

const BASE_URL = 'http://localhost:8080/api/v1';

export const options = {
    vus: 1,
    iterations: 3,
    duration: '20s',
};

export function setup() {
    const token = createUser(100);
    const params = loggedParams(token);

    const events = http.get(`${BASE_URL}/events?page=1&limit=1`, params);
    const eventId = events.json('events.0.id'); 
    const eventOdds = events.json('events.0.odds.0');

    return { token, eventId, eventOdds };
}

export default function (data) {
    const { token, eventId, eventOdds } = data;

    const params = loggedParams(token);

    const betRequest = JSON.stringify({
        eventId: eventId,
        amount: 10,
        outcome: 0,
        odds: eventOdds + 1
    });

    const transactionsInitialCount = http.get(`${BASE_URL}/wallet/transactions?page=1&limit=20`, params).json('transactions.length');

    const responses = http.batch([
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
        ['POST', `${BASE_URL}/bets`, betRequest, params],
    ]);

    check(responses, {
        'No bets succeeded': (resps) => resps.filter(r => r.status === 201).length <= 0,
        'Duplicate bets have same results': (resps) => resps.every(r => r.status === resps[0].status && r.body === resps[0].body),
    });

    const transactionsFinalCount = http.get(`${BASE_URL}/wallet/transactions?page=1&limit=20`, params).json('transactions.length');
    const betsCreated = transactionsFinalCount - transactionsInitialCount;

    const finalBalance = http.get(`${BASE_URL}/wallet/balance`, params).json('balance');
    
    check(finalBalance, {
        'Balance not changed': (balance) => balance === 100,
    });

    check(betsCreated, {
        'No bets created': (count) => count === 0,
    });
}