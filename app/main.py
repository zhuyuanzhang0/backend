from fastapi import FastAPI
from app.api.routes import router
import uvicorn
from fastapi.staticfiles import StaticFiles
from app.db.init import init_bills_db, init_position_db, init_kv_db
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import uuid
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

# init_bills_db()
# init_position_db()
# init_kv_db()

logger = logging.getLogger("app")
app = FastAPI()

@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    now = datetime.now(timezone.utc).isoformat()
    client_ip = _get_client_ip(request)

    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        logger.info(
            '%s ip=%s method=%s path=%s status=%s dur_ms=%.2f ua="%s" referer="%s"',
            now,
            client_ip,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request.headers.get("user-agent", "-"),
            request.headers.get("referer", "-"),
        )



app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8888, reload=True)