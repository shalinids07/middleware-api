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
    allow_headers=["*"],
)


# -----------------------------
# Middleware
# -----------------------------
@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # ---------- Rate Limit ----------
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    history = clients[client_id]

    while history and now - history[0] >= WINDOW:
        history.popleft()

    if len(history) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    history.append(now)

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # Echo request id in RESPONSE HEADER
    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Ping Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }


# -----------------------------
# Root
# -----------------------------
@app.get("/")
async def root():
    return {
        "status": "running"
    }
