import asyncio
from itertools import zip_longest
import requests
from datetime import datetime
from langchain.schema import (
  AIMessage,
  BaseMessage
)

import src.chat.service as chat_service
from src.whatsapp_webhook.schemas.webhook_payload_schema import WaWebhookPayload, WaPayloadEntryChanges
from src.whatsapp_webhook.schemas.api_schema import WaMessageResponseSchema
from src.chat.models.wingman_chat import WingmanChatsModel
from src.config import config
from src.chat.models.wingman_chat import WingmanChatsModel, MessageModel


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
        wa_message_id=message.id,
        created_at=message.timestamp,
      ),
      MessageModel(
        type="text",
        role="assistant",
        content=chat_text_result,
        wa_message_id=whatsapp_response.messages[0].id,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
