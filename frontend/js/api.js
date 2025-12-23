const BASE_URL = 'http://127.0.0.1:5001/api';

const api = {
    async get(endpoint) {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${BASE_URL}${endpoint}`, { headers });
        return res.json();
    },

    async post(endpoint, body) {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body)
        });
        return res.json();
    },

    async del(endpoint) {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${BASE_URL}${endpoint}`, {
            method: 'DELETE',
            headers
        });
        return res.json();
    }
};

function logout() {
    localStorage.clear();
    window.location.href = '/index.html'; // Absolute path is safer if we serve from frontend root
}

function checkAuth(role) {
    if (!localStorage.getItem('token')) window.location.href = '/login.html?role=' + role; // Send to login of that role
    if (role && localStorage.getItem('role') !== role) {
        alert('Unauthorized');
        window.location.href = '/login.html?role=' + role;
    }
}
