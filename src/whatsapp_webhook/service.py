import asyncio
from itertools import zip_longest
import requests
from datetime import datetime
from src.whatsapp_webhook.schemas.webhook_payload_schema import WaWebhookPayload, WaPayloadEntryChanges
from src.whatsapp_webhook.schemas.api_schema import WaMessageResponseSchema
from src.config import config
from src.user.models import UserModel
from src.chat.models import ChatModel, MessageModel
import src.chat.service as chat_service
import src.openai_module.service as openai_service
import src.user.service as user_service
from src.openai_module.schemas import ChatCompletionMessageSchema, ChatCompletionOptionsSchema, ChatCompletionResponseSchema
from src.system_profile.models import SystemProfileModel


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


async def handle_new_messages(change: WaPayloadEntryChanges) -> ChatModel:
  if len(change.value.contacts) == 0:
    return None

  if len(change.value.messages) == 0:
    return None

  metadata = change.value.metadata

  updatedChats = []

  for _, (message, contact) in enumerate(zip_longest(change.value.messages, change.value.contacts)):
    # ? Uneven lengths of message/contact
    if not message or not contact:
        break

    # ? Only handle text messages
    if message.message_type != "text":
        continue

    user = await user_service.get_or_create_user(
      UserModel(
        whatsapp_id=contact.wa_id,
        name=contact.profile.name,
        phone_number=contact.wa_id
      )
    )
    
    user_chat = None

    try:
      user_chat = await chat_service.get_or_create_chat(
        ChatModel(
          user=UserModel(
            whatsapp_id=user.whatsapp_id
          ),
          system_profile=SystemProfileModel(
            whatsapp_id=metadata.phone_number_id
          ),
        )
      );
    except Exception as e:
      print("ERROR", e)
    
    user_name = user.name.split(" ")[0]
    
    chat_history = [] if not user_chat else user_chat.messages
    formatted_chat_history = [
      ChatCompletionMessageSchema(
        role=chat_message.role,
        content=chat_message.content,
        name=user_name
      ) for chat_message in chat_history
    ]
    formatted_chat_history.append(
      ChatCompletionMessageSchema(
        role="user",
        content=message.text.body,
        name=user_name
      )
    )

    chat_completion: ChatCompletionResponseSchema = openai_service.create_full_chat_completion(
      message_history=formatted_chat_history,
      user=user,
      options=ChatCompletionOptionsSchema()
    )

    chat_text_result = "The system is currently unable to generate response"

    if chat_completion:
      chat_text_result = chat_completion.choices[0].message.content
      

    whatsapp_response = send_whatsapp_message(
      contact.wa_id, chat_text_result)

    # TODO: Implement error handling if call to whatsapp failed
    if len(whatsapp_response.messages) == 0:
      continue

    chat_criteria = {
      "system_profile.whatsapp_id": metadata.phone_number_id,
      "user.whatsapp_id": contact.wa_id
    }

    chat_messages = [
      MessageModel(
        role="user",
        content=message.text.body,
        wa_message_id=message.id,
        created_at=message.timestamp,
      ),
      MessageModel(
        role="assistant",
        content=chat_text_result,
        wa_message_id=whatsapp_response.messages[0].id,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      ),
    ]

    updatedChat = await chat_service.upsert_chat_message(chat_criteria, chat_messages)
    updatedChats.append(updatedChat)

  return updatedChats


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
