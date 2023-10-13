
from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Header, Query, status
from src.config import config
from src.whatsapp_webhook.schemas.webhook_payload_schema import WaWebhookPayload
from src.whatsapp_webhook.dependencies import validate_whatsapp_webhook_payload
import src.whatsapp_webhook.service as whatsapp_service

router = APIRouter(tags=["whatsapp-webhook"])

@router.get("/verify")
async def handle_verify_webhook_endpoint(
  hub_mode: Annotated[str, Query(alias="hub.mode")],
  hub_challenge: Annotated[str, Query(alias="hub.challenge")],
  hub_verify_token: Annotated[str, Query(alias="hub.verify_token")],
):
  if (hub_verify_token != config.WHATSAPP_WEBHOOK_VERIFY_TOKEN):
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verification token"
    )

  return hub_challenge


@router.post("/message")
async def handle_whatsapp_event(payload: Annotated[dict, Body()], x_hub_signature_256: Annotated[str, Header()] = None):
  _ = await whatsapp_service.handle_whatsapp_event(WaWebhookPayload(**payload))

  return "OK"
