import socket

_original_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _ipv4_only_getaddrinfo
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import create_tables
from app.config import settings

from app.api import health, reports, sentiment, config, trigger, jobs, runs, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure DB tables exist
    logger.info("Initializing database...")
    create_tables()
    
    # 2. Load deep learning models into memory so they are ready for inference
    from app.services.finbert import load_model as load_finbert
    from app.services.absa import load_model as load_absa
    
    load_finbert(settings.FINBERT_MODEL)
    load_absa(settings.ABSA_MODEL)
    
    # 3. Start local scheduler (optional, primarily for dev without cron-job.org)
    from app.scheduler.jobs import start_scheduler
    start_scheduler()
    
    yield
    
    # Shutdown actions
    logger.info("Shutting down Sentinel...")

app = FastAPI(
    title="Business Intelligence Sentinel API",
    description="Deep Learning Sentiment Correlation & Market Intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(reports.router)
app.include_router(sentiment.router)
app.include_router(config.router)
app.include_router(trigger.router)
app.include_router(jobs.router)
app.include_router(runs.router)
app.include_router(stats.router)
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            return {"detail": "Not Found"}
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
