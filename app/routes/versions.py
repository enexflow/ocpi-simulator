from fastapi import APIRouter
from app.config import config
from app.log_utils import get_logger

logger = get_logger("ocpi-versions")
router = APIRouter()

from fastapi import APIRouter, Request
from datetime import datetime
from app.config import config
from app.log_utils import get_logger

logger = get_logger("versions")
router = APIRouter()

@router.get("/ocpi/versions")
async def get_versions(request: Request):  # ← add Request parameter
    logger.info(f"I AM IN GET VERSIONS ROUTE", direction="CPO->EMSP", module="versions")
    logger.info(f"GET /ocpi/versions called from {request.client.host}")
    logger.info(f"Headers: {dict(request.headers)}")
    base = f"http://{config._config.get('host_url', '127.0.0.1')}:{config._config.get('port', 8000)}"
    return {
        "status_code": 1000,
        "status_message": "Success",
        "timestamp": datetime.utcnow().isoformat(),
        "data": [
            {
                "version": "2.2.1",
                "url": f"{base}/ocpi/emsp/2.2.1"
            }
        ]
    }

@router.get("/ocpi/emsp/2.2.1")
async def get_version_details(request: Request):
    logger.info(f"I AM IN GET VERSION DETAILS ROUTE", direction="CPO->EMSP", module="versions")
    logger.info(f"GET /ocpi/emsp/2.2.1 called from {request.client.host}")
    logger.info(f"Headers: {dict(request.headers)}")
    base_url = f"http://{config._config.get('host_url', '127.0.0.1')}:{config._config.get('port', 8000)}/ocpi/emsp/2.2.1"
    
    return {
        "status_code": 1000,
        "status_message": "Success",
        "timestamp": "2026-01-01T00:00:00Z",
        "data": {
            "version": "2.2.1",
            "endpoints": [
                {
                    "identifier": "credentials",
                    "role": "SENDER",
                    "url": f"{base_url}/credentials"
                },
                {
                    "identifier": "locations",
                    "role": "RECEIVER",
                    "url": f"{base_url}/locations"
                },
                {
                    "identifier": "cdrs",
                    "role": "RECEIVER",
                    "url": f"{base_url}/cdrs"
                }
            ]
        }
    }
