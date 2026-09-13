import uuid
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import APP_NAME, APP_VERSION, REQUEST_ID_HEADER, validate_config, HOST, PORT
from app.core.logging_config import app_logger, request_id_var
from app.api.routes import router
from app.services.jobs import get_job_manager
from app.services.manifest import IndexManifest

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Validate configuration, recover stale background jobs, and validate index manifest
    try:
        validate_config()
        app_logger.info(f"Starting {APP_NAME} v{APP_VERSION} - Configuration validated successfully.")
        get_job_manager().recover_stale_jobs()
        IndexManifest().validate()
    except Exception as e:
        app_logger.error(f"Startup recovery/validation warning: {e}", exc_info=True)
    yield
    app_logger.info(f"Shutting down {APP_NAME}.")

app = FastAPI(
    title=APP_NAME,
    description="Production-grade RAG-based Academic Assistant API",
    version=APP_VERSION,
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID & Logging Middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    # Extract or generate Request ID
    req_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    token = request_id_var.set(req_id)
    request.state.request_id = req_id

    try:
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = req_id
        return response
    finally:
        request_id_var.reset(token)

# Include API routes
app.include_router(router)

@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
