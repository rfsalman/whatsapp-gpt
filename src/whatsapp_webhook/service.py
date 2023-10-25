import asyncio
import requests
import aiohttp
from fastapi import HTTPException, status
from bson import ObjectId
from itertools import zip_longest
from datetime import datetime
from langchain.schema import (
  AIMessage,
  BaseMessage
)

import src.chat.service as chat_service
import src.user.service as user_service
from src.whatsapp_webhook.schemas.webhook_payload_schema import WaWebhookPayload, WaPayloadEntryChanges
from src.whatsapp_webhook.schemas.api_schema import WaMessageResponseSchema
from src.chat.models.wingman_chat import WingmanChatsModel
from src.config import config
from src.chat.models.wingman_chat import WingmanChatsModel, MessageModel, WhatsappMessageMetadata
from src.whatsapp_webhook.schemas.activation_message import UserActivationMessageDto
from src.exceptions import (
  BaseException,
  InternalServerError, 
  NotFoundError
)


async def handle_whatsapp_event(data: WaWebhookPayload):
  logs = []

  for entry in data.entry:
    messageChanges = [
      change for change in entry.changes if change.field == "messages"
    ]
    messageTasks = [handle_new_messages(change) for change in messageChanges]

    messageResults = await asyncio.gather(*messageTasks)

    logs.extend(item for item in messageResults)

  return logs

async def handle_new_messages(change: WaPayloadEntryChanges) -> list[WingmanChatsModel]:
  if len(change.value.contacts) == 0:
    return None

  if len(change.value.messages) == 0:
    return None

  updated_chats = []

  for _, (message, contact) in enumerate(zip_longest(change.value.messages, change.value.contacts)):
    # ? Uneven lengths of message/contact
    if not message or not contact:
      break

    # ? Only handle text messages
    if message.message_type != "text":
      continue

    wingman_chat: WingmanChatsModel = None
    chat_completion: AIMessage = None
    chat_history: list[BaseMessage] = []

    try:
      wingman_chat, chat_completion, chat_history = await chat_service.handle_chat_message_pipeline(
        message=message,
        contact=contact,
      )
    except Exception as e:
      print("Error in message pipeline", e)    

    chat_text_result = "The system is currently unable to generate response"

    if chat_completion:
      chat_text_result = chat_completion.content

    whatsapp_response = send_whatsapp_message(
      contact.wa_id, chat_text_result)

    # TODO: Implement error handling if call to whatsapp failed
    if len(whatsapp_response.messages) == 0:
      continue
    
    if not wingman_chat:
      continue

    chat_messages = [
      MessageModel(
        type="text",
        role="user",
        content=message.text.body,
        created_at=message.timestamp,
        whatsapp_message_metadata=WhatsappMessageMetadata(
          wa_message_id=message.id,
        )
      ),
      MessageModel(
        type="text",
        role="assistant",
        content=chat_text_result,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        whatsapp_message_metadata=WhatsappMessageMetadata(
          wa_message_id=whatsapp_response.messages[0].id,
        )
      ),
    ]

    updated_chat = await chat_service.upsert_chat_message({"_id": wingman_chat.id}, chat_messages)
    updated_chats.append(updated_chat)

    history_length = len([*chat_history, *chat_messages])

    if history_length >= 10:
      _ = await chat_service.create_latest_chat_summary(wingman_chat_id=str(updated_chat.id))

  return updated_chats

def send_whatsapp_message(to: str, content: str) -> WaMessageResponseSchema:
  url = "{}/messages".format(config.FACEBOOK_API_URL)

  headers = {
    "Authorization": "Bearer {}".format(config.WHATSAPP_ACCESS_TOKEN),
    "Content-Type": "application/json"
  }

  data = {
    "type": "text",
    "messaging_product": "whatsapp",
    "to": to,
    "text": {
      "body": content
    },
  }

  response = requests.post(url, headers=headers, json=data)

  responseBody = response.json()

  return WaMessageResponseSchema(**responseBody)

async def send_whatsapp_user_activation_message(dto: UserActivationMessageDto) -> WaMessageResponseSchema:
  try:
    user = await user_service.get_user({
      "_id": ObjectId(dto.user_id)
    })

    if not user:
      raise NotFoundError(
        detail={
          "user._id": [f"Can't find user with id {dto.user_id}"]
        }
      )

    if not user.phone_number:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
          "user.phone_number": ["User has not registered their phone number"]
        }
      )
    
    if user.verified:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
          "user.verified": ["User already verified"]
        }
      )  


    wingman_chat = await chat_service.get_or_create_chat(
      {
        "user_id": user.id,
        "wingman_assistant_id": user.selected_wingman_id
      }
    )

    if not wingman_chat:
      raise NotFoundError(
        detail={
          "wingman_chat._id": ["Can't find wingman_chat for this user"]
        }
      )
    
    whatsapp_messaging_url = f"{config.FACEBOOK_API_URL}/messages"
    headers = {
      "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
      "Content-Type": "application/json"
    }

    message_body_parameters = []    

    if dto.message_template != config.WA_TEMPLATE_USER_VERIFICATION:
      message_body_parameters.append(
        {
          "type": "text",
          "text": user.bio.full_name if user.bio and user.bio.full_name else "Wingman User"
        }
      )

    payload = {
      "messaging_product": "whatsapp",
      "recipient_type": "individual",
      "to": user.phone_number,
      "type": "template",
      "template": {
        "name": dto.message_template,
        "language": {
          "code": "en"
        },
        "components": [
          {
            "type": "body",
            "parameters": message_body_parameters
          },
          {
            "type": "button",
            "sub_type": "url",
            "index": "0",
            "parameters": [
              {
                "type": "text",
                "text": f"?{dto.activation_link_query_string}"
              }
            ]
          }
        ]
      }
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
      async with session.post(
        url=whatsapp_messaging_url,
        json=payload  
      ) as response:
        json_res = await response.json()
        response_data = WaMessageResponseSchema(**json_res)

    if response_data and len(response_data.messages) > 0:
      _ = await chat_service.upsert_chat_message(
        chat_data={
          "_id": wingman_chat.id
        },
        messages=[
          MessageModel(
            type="user-activation-link",
            role="assistant",
            content="",
            whatsapp_message_metadata=WhatsappMessageMetadata(
              wa_message_id=response_data.messages[0].id
            ) 
          )
        ]
      )

    return response_data

  except BaseException as e:
    print("BASE EXCEPTION", e)
    
    raise e

  except HTTPException as e:
    raise e

  except Exception as e:
    print("EXCEPTION", e)
    
    raise InternalServerError(
      detail={
        "system": [str(e)]
      }
    )
  

