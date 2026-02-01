# 🔧 Analytics Dashboard Troubleshooting Guide

## Problem: "Failed to Fetch" Error in Analytics Tab

### Quick Fixes (Try these in order):

---

## ✅ Fix 1: Make Sure You're Logged In

**The analytics page requires ADMIN authentication.**

1. Go to `http://localhost:8000/login.html`
2. Login with admin credentials:
   - Email: `admin@hospital.com`
   - Password: (your admin password)
3. After successful login, go to `http://localhost:8000/admin/dashboard.html`
4. Click "📊 Analytics" in the sidebar

**Why this fixes it:** The API endpoints require a valid admin token.

---

## ✅ Fix 2: Check if Backend is Running

**The Flask backend must be running on port 5001.**

### Check if it's running:
Open PowerShell and run:
```powershell
curl http://127.0.0.1:5001/api/analytics/summary
```

### If you get an error (connection refused):
The backend is NOT running. Start it:
```powershell
cd backend
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5001
* Debugger is active!
```

---

## ✅ Fix 3: Check Browser Console for Errors

1. Open the analytics page
2. Press `F12` to open browser developer tools
3. Click the "Console" tab
4. Look for error messages

### Common errors and fixes:

**Error: "401 Unauthorized"**
- **Fix:** You're not logged in. Go back to Fix 1.

**Error: "404 Not Found"**
- **Fix:** The analytics routes aren't registered. Restart the backend.

**Error: "Failed to fetch" or "Network Error"**
- **Fix:** Backend is not running. Go to Fix 2.

**Error: "CORS policy"**
- **Fix:** Add this to backend/app.py (already done, but verify):
  ```python
  CORS(app, resources={r"/*": {"origins": "*"}})
  ```

---

## ✅ Fix 4: Clear Browser Cache

Sometimes old JavaScript files are cached.

1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"
4. Refresh the page (`Ctrl + F5`)

---

## ✅ Fix 5: Verify File Paths

Make sure these files exist:
- `frontend/js/api.js`
- `frontend/admin/analytics.html`
- `backend/routes/analytics.py`

Check that `api.js` is being loaded (look in browser dev tools > Network tab)

---

## 🔍 Detailed Debugging Steps

### Step 1: Check the Console Logs

After opening the analytics page and pressing F12, you should see:
```
Starting to load analytics...
API Base URL: http://127.0.0.1:5001/api
Token: eyJ... (your token)
[API GET] http://127.0.0.1:5001/api/analytics/summary
[API Response] 200 OK
Fetching summary statistics...
```

### Step 2: Test API Directly

Open a new browser tab and go to:
```
http://127.0.0.1:5001/api/analytics/summary
```

**If you see JSON data:**
✅ Backend is working!

**If you see login page or 401:**
❌ You need to login first

**If you see "Cannot connect":**
❌ Backend is not running

---

## 🎯 Most Common Solution

**99% of "Failed to fetch" errors are because:**

1. **Backend is not running** (Fix: Start it with `python backend/app.py`)
2. **Not logged in as admin** (Fix: Login at `/login.html` first)

---

## 📞 Still Not Working?

If none of the above fixes work, please provide:

1. Screenshot of the browser console (F12 > Console tab)
2. Screenshot of the error message
3. Output from backend terminal
4. Which URL you're accessing (port 8000 or 5001?)

---

## ✅ Success Checklist

Before accessing analytics, make sure:
- [ ] Backend is running on port 5001
- [ ] You're logged in as admin
- [ ] You accessed dashboard from port 8000
- [ ] Browser console shows no errors
- [ ] Token is present in localStorage

---

## 🚀 Quick Test

Run this in browser console (F12 > Console):
```javascript
console.log('Token:', localStorage.getItem('token'));
console.log('Role:', localStorage.getItem('role'));
```

**Expected output:**
```
Token: eyJhbGc... (long string)
Role: admin
```

If you see `null`, you're not logged in!

---

**Last Updated:** February 1, 2026
