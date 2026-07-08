from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from collections import defaultdict, deque
import uuid
import time

app = FastAPI()

EMAIL = "23f1000746@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-0jnmtr.example.com",
    "https://exam.sanand.workers.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT = 15
WINDOW = 10

clients = defaultdict(deque)


@app.middleware("http")
async def middleware(request: Request, call_next):

    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    q = clients[client]

    while q and now - q[0] >= WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    q.append(now)

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }


@app.get("/")
async def root():
    return {"status": "ok"}
