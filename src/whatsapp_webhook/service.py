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

    user = await user_service.get_user({"whatsapp_id": contact.wa_id})

    if not user:
        userData = UserModel(
            whatsapp_id=contact.wa_id,
            name=contact.profile.name,
            phone_number=contact.wa_id
        )

        user = await user_service.create_user(userData)

    finish_reason = ""
    chatCompletionTextResult = ""

    while finish_reason in ["", "length"]:
      messages = [
        ChatCompletionMessageSchema(
          role="system",
          content="""
            You are Madeline, everyone's helpful assistant, 
            DO NOT reveal that you are OpenAI or any other AI model
          """,
          name="Madeline"
        ),
        ChatCompletionMessageSchema(
          role="user",
          content=message.text.body,
          name=user.name.split(" ")[0]
        )
      ]

      if finish_reason == "length":
        messages.append(
          ChatCompletionMessageSchema(
            role="assistant",
            content=chatCompletionTextResult,
            name=metadata.display_phone_number
          ),
        )
        messages.append(ChatCompletionMessageSchema(
          role="user",
          content="continue",
          name=user.name.split(" ")[0]
        ))

      chatCompletion: ChatCompletionResponseSchema = openai_service.create_chat_completion(
        messages=messages,
        options=ChatCompletionOptionsSchema()
      )

      finish_reason = chatCompletion.choices[0].finish_reason
      chatCompletionTextResult = chatCompletionTextResult + \
        chatCompletion.choices[0].message.content

      whatsappResponse = send_whatsapp_message(
        contact.wa_id, chatCompletionTextResult)

      # TODO: Implement error handling if call to whatsapp failed
      if len(whatsappResponse.messages) == 0:
        continue

      chatCriteria = {
        "system_profile.whatsapp_id": metadata.phone_number_id,
        "user.whatsapp_id": contact.wa_id
      }

      chatMessages = [
        MessageModel(
          role="user",
          content=message.text.body,
          wa_message_id=message.id,
          created_at=message.timestamp,
        ),
        MessageModel(
          role="assistant",
          content=chatCompletionTextResult,
          wa_message_id=whatsappResponse.messages[0].id,
          created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
      ]

      updatedChat = await chat_service.createChatMessage(chatCriteria, chatMessages)
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
