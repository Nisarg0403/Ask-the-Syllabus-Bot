import logging
import json
import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from app.core.config import LOG_LEVEL, STRUCTURED_LOGGING_ENABLED

# ContextVar for propagating request_id across async callstacks
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class StructuredJsonFormatter(logging.Formatter):
    """
    JSON Log Formatter for structured telemetry without exposing sensitive content.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include request_id if available
        req_id = request_id_var.get()
        if req_id:
            log_data["request_id"] = req_id

        # Attach extra structured attributes attached via logger
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            # Exclude full document content or raw prompts if present
            safe_extra = {
                k: v for k, v in record.extra_data.items()
                if k not in ("document_content", "raw_prompt", "full_response", "api_key", "password")
            }
            log_data.update(safe_extra)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging():
    """Configures application-wide logging."""
    logger = logging.getLogger("rag_app")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Avoid adding duplicate handlers if re-initialized
    if not logger.handlers:
        handler = logging.StreamHandler()
        if STRUCTURED_LOGGING_ENABLED:
            handler.setFormatter(StructuredJsonFormatter())
        else:
            handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s"))
        logger.addHandler(handler)
        
    return logger

app_logger = setup_logging()
