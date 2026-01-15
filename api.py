"""
FastAPI Wrapper for AI Log Analysis System
Provides an HTTP interface on port 3452 to trigger analysis and check health.
"""

import uvicorn
from fastapi import FastAPI, Query, BackgroundTasks
from typing import Optional, List
from orchestrator.orchestrator import Orchestrator
from utils.logger import get_logger
import traceback
from utils.exceptions import AgenticLogAnalysisException

# Initialize logger
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Log Analysis System API",
    description="API to trigger log analysis and check system health",
    version="1.0.0"
)

# Initialize Orchestrator
# Note: Orchestrator initialization might fail if env vars are missing
orchestrator_error = None
try:
    orchestrator = Orchestrator()
except AgenticLogAnalysisException as e:
    error_msg = f"{e.message}: {e.details}"
    logger.error(f"Failed to initialize orchestrator: {error_msg}")
    logger.error(traceback.format_exc())
    orchestrator_error = error_msg
    orchestrator = None
except Exception as e:
    logger.error(f"Failed to initialize orchestrator: {e}")
    logger.error(traceback.format_exc())
    orchestrator_error = str(e)
    orchestrator = None

@app.get("/")
async def root():
    return {"message": "AI Log Analysis System API is running"}

@app.get("/health")
async def health_check():
    """Perform health check on all components"""
    if not orchestrator:
        return {"status": "unhealthy", "error": f"Orchestrator not initialized: {orchestrator_error}"}
    
    return orchestrator.health_check()

@app.post("/run")
async def run_analysis(
    background_tasks: BackgroundTasks,
    hours: int = Query(24, description="Hours of logs to analyze"),
    service: Optional[str] = Query(None, description="Comma-separated list of services"),
    severity: Optional[str] = Query(None, description="Comma-separated list of severities"),
    no_email: bool = Query(False, description="Skip sending email alert")
):
    """Trigger a manual log analysis run"""
    if not orchestrator:
        return {"status": "error", "message": f"Orchestrator not initialized: {orchestrator_error}"}
    
    # Parse filters
    service_filter = service.split(",") if service else None
    severity_filter = severity.split(",") if severity else None
    
    # Run in background to avoid timeout
    background_tasks.add_task(
        orchestrator.run_analysis,
        hours=hours,
        service_filter=service_filter,
        severity_filter=severity_filter,
        send_email=not no_email
    )
    
    return {
        "status": "accepted",
        "message": f"Analysis triggered for the last {hours} hours",
        "filters": {
            "service": service_filter,
            "severity": severity_filter,
            "send_email": not no_email
        }
    }

if __name__ == "__main__":
    # Get port from environment or use default 3452
    import os
    port = int(os.getenv("API_PORT", 3452))
    uvicorn.run(app, host="0.0.0.0", port=port)
