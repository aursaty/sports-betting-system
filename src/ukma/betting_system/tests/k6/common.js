import http from 'k6/http';

const BASE_URL = 'http://localhost:8080/api/v1';

export function createUser(balance = 100) {
    const email = `testuser_${Date.now()}@example.com`;
    const password = 'password123';

    http.post(`${BASE_URL}/auth/register`, JSON.stringify({ email, password }), { headers: { 'Content-Type': 'application/json' } });

    const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({ email, password }), { headers: { 'Content-Type': 'application/json' } });
    const token = loginRes.json('token'); 

    const params = loggedParams(token);

    if(balance > 0){
        http.post(`${BASE_URL}/wallet/deposit`, JSON.stringify({ amount: balance }), params);
    }

    return token;
}

export function loggedParams(token){
    const params = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
    };
    return params;
}