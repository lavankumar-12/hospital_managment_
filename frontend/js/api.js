// Determine API URL based on where we are running
// If running on localhost but NOT on port 5001, assume we are in dev mode (e.g. port 8000) and need to point to port 5001.
// Otherwise (production or running directly on backend port 5001), use relative path.
const BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '5001'
    ? 'http://127.0.0.1:5001/api'
    : '/api';

const api = {
    async get(endpoint) {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        try {
            const url = `${BASE_URL}${endpoint}`;
            console.log('[API GET]', url);
            const res = await fetch(url, { headers });
            console.log('[API Response]', res.status, res.statusText);

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`HTTP ${res.status}: ${errorText || res.statusText}`);
            }

            return res.json();
        } catch (error) {
            console.error('[API Error]', endpoint, error);
            throw error;
        }
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
