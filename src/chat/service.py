
from src.databases.mongo import db
from .models import ChatModel, MessageModel
from src.models import PyObjectId


async def getChat(chatCriteria: dict) -> ChatModel:
  if chatCriteria["_id"]:
    chatCriteria["_id"] = PyObjectId(chatCriteria["_id"])

  chat = await db["chats"].find_one(chatCriteria)

  return ChatModel(**chat)


async def createChatMessage(chatData: dict, messages: list[MessageModel]) -> ChatModel:
  updated = await db["chats"].update_one(
    chatData,
    {
      "$push": {
        "messages": {
          "$each": [message.dict() for message in messages]
        }
      }
    },
    upsert=True
  )

  chat = await db["chats"].find_one({"_id": updated.upserted_id})

  return chat
