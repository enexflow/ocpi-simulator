import base64
from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
from app.config import config
from app.state import state
from app.validators.validate import validate_payload
from datetime import datetime
from app.log_utils import get_logger
import uuid


logger = get_logger("ocpi-credentials")
router = APIRouter()


def _maybe_b64decode_token(token: str) -> str:
    try:
        return base64.b64decode(token).decode("utf-8")
    except Exception:
        return token


@router.post("/ocpi/emsp/2.2.1/credentials")
async def post_credentials(
    request: Request,
    authorization: str = Header(None),
):
    """
    OCPI Credentials Exchange (Receiver / Server Side).
    1. Validate Authorization header (Bootstrap or previous token).
    2. Validate payload schema.
    3. Store new token and endpoints.
    4. Return our credentials.
    """

    # 1. Header Validation using Bootstrap token logic
    expected_token = config.bootstrap_token
    logger.info(f"EXPECTED TOKEN: {expected_token}", direction="CPO->EMSP", module="credentials")
    raw_auth_token = authorization.replace("Token ", "").strip() if authorization else ""
    auth_token = _maybe_b64decode_token(raw_auth_token)
    logger.info(f"AUTH TOKEN: {auth_token}", direction="CPO->EMSP", module="credentials")

    if auth_token != expected_token and auth_token != state.cpo_token_to_emsp:
        logger.warning(
            "Invalid Authorization Token",
            direction="CPO->EMSP",
            module="credentials",
            context=f"Token={raw_auth_token}",
        )
        return {
            "status_code": 2001,
            "status_message": "Invalid or missing Authorization header",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {},
        }

    # 2. Schema Validation
    try:
        payload = await request.json()
    except Exception:
        logger.error("Invalid JSON Body", direction="CPO->EMSP", module="credentials")
        return {
            "status_code": 2001,
            "status_message": "Invalid JSON",
            "timestamp": datetime.utcnow().isoformat(),
        }

    is_valid, errors = validate_payload(payload, "credentials")
    if not is_valid:
        logger.error(
            "Schema validation failed",
            direction="CPO->EMSP",
            module="credentials",
            context=f"Errors={errors}",
        )
        return JSONResponse(
            status_code=config.validation_error_http_status,
            content={
                "status_code": 2001,
                "status_message": "Schema validation failed",
                "data": {"errors": errors},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    # 3. Store Data
    new_emsp_token_to_cpo = payload.get("token")
    if new_emsp_token_to_cpo:
        state.emsp_token_to_cpo = new_emsp_token_to_cpo
        logger.info(
            "Handshake successful. Received token to call CPO.",
            direction="CPO->EMSP",
            module="credentials",
            context=f"Token={new_emsp_token_to_cpo[:4]}***",
        )

    state.cpo_url = payload.get("url")  # Base URL of CPO

    # 4. Return Our Credentials
    # base_url = f"http://{config._config.get('host_url', '127.0.0.1')}:{config._config.get('port', 8000)}/ocpi/emsp/2.2.1"

    token_c = str(uuid.uuid4())
    state.cpo_token_to_emsp = token_c  # save it for future requests

    base_url = f"http://{config._config.get('host_url', '127.0.0.1')}:{config._config.get('port', 8000)}"

    response_data = {
        "token": token_c,
        "url": f"{base_url}/ocpi/versions",
        "roles": [
            {
                "role": "EMSP",
                "party_id": "XCO",
                "country_code": "NL",
                "business_details": config.business_details,
            }
        ],
    }
    return {
        "status_code": 1000,
        "status_message": "Success",
        "timestamp": datetime.utcnow().isoformat(),
        "data": response_data,
    }