# Khau Katta (खाऊ कट्टा) — Smart Canteen Pre-Order & Queue App

## Project structure
```
khau-katta/
  backend/           FastAPI + SQLite (swap to Postgres for production)
    app/
      main.py         app entrypoint, CORS, websocket, seed data
      models.py        SQLAlchemy models (MenuItem, Order, OrderItem)
      schemas.py        Pydantic request/response schemas
      prediction.py      AI-style ETA & rush-level prediction logic
      ws_manager.py        WebSocket broadcast manager
      routers/
        menu.py        GET/POST /menu
        orders.py        POST /orders, /orders/group, PATCH status, GET
        queue.py         GET /queue/status
    requirements.txt
    Dockerfile
  frontend/           Plain HTML/CSS/JS (no build step needed)
    index.html
    style.css
    app.js
```

## Run locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
This starts the API on `http://localhost:8000`, auto-creates `khau_katta.db`
(SQLite), and seeds a starter menu. Interactive API docs at
`http://localhost:8000/docs`.

**Frontend**
```bash
cd frontend
python -m http.server 5500
```
Open `http://localhost:5500`. If your backend runs elsewhere, update
`API_BASE` at the top of `app.js`.

## How the AI prediction works
`backend/app/prediction.py` estimates each order's prep time from the
slowest item in the order plus a queue-delay term based on how many orders
are already pending (assumes the kitchen can work on a few items in
parallel). `rush_level()` classifies current load as Low/Medium/High. This
is a transparent heuristic on purpose — swap `estimate_prep_time()` for a
trained scikit-learn/regression model later without touching any callers,
once you've logged enough real order history.

## Deploying

**Backend (Render / Railway)**
1. Push this repo to GitHub.
2. Create a new Web Service from the repo, root directory `backend`.
3. It will build from the included `Dockerfile` automatically (or set the
   start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
4. For production, set `DATABASE_URL` to a managed Postgres connection
   string (Render/Railway/Neon/Supabase) — the code already reads it from
   the environment and falls back to SQLite if unset.
5. Note the deployed URL, e.g. `https://khau-katta-api.onrender.com`.

**Frontend (Vercel / Netlify)**
1. Update `API_BASE` and `WS_BASE` in `frontend/app.js` to your deployed
   backend URL.
2. Deploy the `frontend` folder as a static site (no build command needed).
3. In `backend/app/main.py`, tighten `allow_origins` in the CORS
   middleware to your deployed frontend domain instead of `"*"`.

## Next steps worth adding
- JWT auth for students/admins (register/login endpoints)
- Admin dashboard UI to change order status and see analytics
- QR-code generation for pickup verification
- scikit-learn model trained on real order-history data for sharper ETAs
