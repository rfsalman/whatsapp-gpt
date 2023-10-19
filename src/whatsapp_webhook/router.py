
from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Header, Query, status

import src.whatsapp_webhook.service as whatsapp_service
from src.schemas.api_response import ApiResponse
from src.config import config
from src.service_users.dependencies.authorization import authorize_service_user
from src.service_users.models.service_user import ServiceUserModel
from src.whatsapp_webhook.schemas.api_schema import WaMessageResponseSchema
from src.whatsapp_webhook.schemas.webhook_payload_schema import WaWebhookPayload
from src.whatsapp_webhook.schemas.activation_message import UserActivationMessageDto
from src.exceptions import (
  BaseException,
  NotFoundError,
)

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

@router.post("/activation-message")
async def handle_send_activation_message(
  _: Annotated[ServiceUserModel, Depends(authorize_service_user)],
  activation_message_dto: UserActivationMessageDto 
):
  try:
    data = await whatsapp_service.send_whatsapp_user_activation_message(
      activation_message_dto
    )

    return ApiResponse[WaMessageResponseSchema](
      status="success",
      code=status.HTTP_200_OK,
      data=data,
      message="Message sent successfully"
    )
  
  except NotFoundError as e:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=e.detail
    )
  
  except BaseException as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=e.detail
    )
  
  except HTTPException as e:
    raise e
  
  except Exception as e:
    print("Exception", e)
    
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail={
        "system": [str(e)]
      }
    )
