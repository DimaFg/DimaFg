from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import ErrorResponse
from app.core.security import hmac_digest
from app.modules.leads.schemas import LeadCreate, LeadCreated
from app.modules.leads.service import create_lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post(
    "",
    response_model=LeadCreated,
    status_code=201,
    responses={
        200: {"model": LeadCreated, "description": "Повторная отправка той же заявки"},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
def submit_lead(
    data: LeadCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$"),
    ] = None,
) -> LeadCreated:
    client_ip = request.client.host if request.client else None
    ip_hash = hmac_digest(client_ip, "lead-ip") if client_ip else None
    result = create_lead(db, data, ip_hash=ip_hash, idempotency_key=idempotency_key)
    if not result.created:
        response.status_code = 200
    return LeadCreated(
        public_number=result.lead.public_number,
        expected_response=get_settings().lead_expected_response,
    )
