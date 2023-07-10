
from src.databases.mongo import db
from .models import ChatModel, MessageModel
from src.models import PyObjectId


async def get_or_create_chat(chat_dto: ChatModel) -> ChatModel:
  chat_data = chat_dto.dict()

  chat = await get_chat(chat_data)

  if not chat:
    chat = await upsert_chat_message(chat_dto.dict(), [])

  return chat


async def get_chat(chat_data: dict) -> ChatModel | None:
  if chat_data.get("_id", None):
    chat_data["_id"] = PyObjectId(chat_data["_id"])

  chat = await db["chats"].find_one(chat_data)
  
  if chat:
    return ChatModel(**chat)

  return  None

async def upsert_chat_message(chat_data: dict, messages: list[MessageModel]) -> ChatModel | None:
  updated = await db["chats"].update_one(
    chat_data,
    {
      "$push": {
        "messages": {
          "$each": [{
            "_id": message.id,
            "wa_message_id": message.wa_message_id,
            "content": message.content,
            "role": message.role,
            "created_at": message.created_at,
          } for message in messages]
        }
      }
    },
    upsert=True
  )

  chat = await db["chats"].find_one({"_id": updated.upserted_id})

  if not chat:
    return None

  return ChatModel(**chat)
