from fastapi import FastAPI
from app.api.routes import router
import uvicorn
from fastapi.staticfiles import StaticFiles
from app.db.init import init_bills_db, init_position_db, init_kv_db
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

# init_bills_db()
# init_position_db()
# init_kv_db()

app = FastAPI()
from uvicorn.config import LOGGING_CONFIG    
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelprefix)s %(message)s"


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