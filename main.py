from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from collections import defaultdict, deque
import uuid
import time

app = FastAPI()

EMAIL = "23f1000746@ds.study.iitm.ac.in"

RATE_LIMIT = 15
WINDOW = 10

clients = defaultdict(deque)

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-0jnmtr.example.com",
        "https://exam.sanand.workers.dev"
    ],
    allow_credentials=False,
    allow_methods=["*"],
allow_headers=[
    "X-Client-Id",
    "X-Request-ID",
    "Content-Type"
],    expose_headers=["X-Request-ID"],
)

# -----------------------------
# Middleware
# -----------------------------
@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # Skip OPTIONS requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Request ID first
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    # Rate limiting only for /ping
    if request.url.path == "/ping":
        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()
        history = clients[client_id]

        while history and now - history[0] > WINDOW:
            history.popleft()

        if len(history) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"X-Request-ID": request_id},
            )

        history.append(now)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
# -----------------------------
# Ping Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):

    request_id = request.state.request_id

    return JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request_id
        },
        headers={
            "X-Request-ID": request_id
        }
    )

# -----------------------------
# Root
# -----------------------------
@app.get("/")
async def root():
    return {
        "status": "running"
    }
