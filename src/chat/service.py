
from datetime import datetime
from typing import Tuple
from bson import ObjectId
from langchain.schema import (
  AIMessage,
  BaseMessage,
  HumanMessage
)

import src.user.service as user_service
import src.openai_module.service as openai_service
import src.cohere_module.service as cohere_service
from src.chat.models.summary import ChatSummaryModel
from src.databases.mongo import db
from .models import ChatModel, MessageModel
from src.user.models import UserModel
from src.whatsapp_webhook.schemas.webhook_payload_schema import (
  WaMessage,
  WaContact,
  WaPayloadMetadata
)
from src.databases.vector import vector_db
from src.utils.dict import flatten_dict
from src.prompts.chat_summary import summary_parser_prompt_template
from src.prompts.wingman import (
  wingman_introduction_prompt,
  wingman_general_prompt,
)
from src.chat.schemas.summary import ChatSummarySchema

async def get_or_create_chat(chat_criteria: dict) -> ChatModel:
  try:
    chat = await find_one_chat(chat_criteria, {"messages": 0})

    if not chat:
      chat = await create_chat(ChatModel(**chat_criteria))
      
    return chat
  except Exception as e:
    raise e  

async def create_chat(chat_dto: ChatModel) -> ChatModel:
  try:
    inserted = await db["chats"].insert_one({
      "_id": chat_dto.id,
      "user": chat_dto.user.dict(),
      "system_profile": chat_dto.system_profile.dict(),
      "messages": []
    })

    chat = await find_one_chat({"_id": inserted.inserted_id}, {"messages": 0})

    return chat
  except Exception as e:
    print("Error at create_chat", e)
    
    raise e

async def find_one_chat(chat_crit: dict, fields: dict = None):
  try:
    if chat_crit.get("_id", None):
      chat_crit["_id"] = ObjectId(chat_crit["_id"])
    
    chat_crit = flatten_dict(chat_crit)
    chat_data = await db["chats"].find_one(chat_crit, fields)

    if not chat_data:
      return None

    return ChatModel(**chat_data)
  except Exception as e:
    raise e

async def get_chat_aggregated(
  chat_criteria: dict, 
  messages_criteria: dict, 
  n_messages: int
) -> ChatModel | None:
  try:
    if chat_criteria.get("_id", None):
      chat_criteria["_id"] = ObjectId(chat_criteria["_id"])
    
    chat_criteria = flatten_dict(chat_criteria)

    pipeline = [
      stage for stage in [
        {"$match": chat_criteria},
        {"$unwind": {"path": "$messages", "preserveNullAndEmptyArrays": True}},
        {"$match": messages_criteria},
        {"$sort": {"messages.created_at": -1}},
        {"$limit": n_messages} if isinstance(n_messages, int) and n_messages > 0 else None,
        {"$group": {
          "_id": "$_id",
          "system_profile": { "$first": "$system_profile" },
          "user": { "$first": "$user" },
          "messages": {"$push": "$messages"}
        }}
      ] if stage is not None
    ]

    chat = await db["chats"].aggregate(pipeline).to_list(length=1)

    if chat:
      chat = ChatModel(**(chat[0]))

      chat.messages = chat.messages[::-1] if chat.messages else []
            
      return chat

    return None
  except Exception as e:
    print("Error at get_chat", e)
    
    raise e

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

  chat = await find_one_chat(chat_data)

  if not chat:
    return None

  return chat

async def handle_chat_message_pipeline(
  message: WaMessage, 
  contact: WaContact,
  metadata: WaPayloadMetadata
) -> tuple[AIMessage, list[BaseMessage]]:
  try:
    # * Get/Create user
    user = await user_service.get_or_create_user(
      {
        "whatsapp_id": contact.wa_id,
        "phone_number": contact.wa_id
      }
    )

    # * Get/Create chat
    user_chat = await get_or_create_chat({
      "user":  {
        "whatsapp_id": user.whatsapp_id,
      },
      "system_profile": {
        "whatsapp_id": metadata.phone_number_id
      }
    });

    summaries = find_last_chat_summaries(str(user_chat.id))

    last_summary = None

    if len(summaries) > 0:
      last_summary = summaries[0]

    # * Get chat with most recent messages after last summary
    aggregated_chat = await get_chat_aggregated(
      chat_criteria={
        "_id": user_chat.id,
      },
      messages_criteria={
        "messages._id": {
          "$gte": ObjectId(last_summary["batch_id"])
        } 
      } if last_summary else {},
      n_messages=10
    )

    # * No new messages after last summary
    if not aggregated_chat:
      aggregated_chat = user_chat

    # * Format chat history into langchain chat prompt
    chat_history = format_chat_history(aggregated_chat, user)
    new_message = HumanMessage(content=message.text.body)
    
    # * Intent classification
    chat_completion: AIMessage = get_chat_response(
      chat_history=chat_history,
      new_message=new_message,
      user=user,
      summaries=summaries
    )

    return (chat_completion, chat_history)
    
  except Exception as e:
    print("Error at handle msg pipeline", e)
    
    raise e
  
def get_chat_response(
  chat_history: list[AIMessage | HumanMessage],
  new_message: AIMessage | HumanMessage, 
  user: UserModel,
  summaries: list[dict] = [],
) -> AIMessage:
  try:
    prompt = wingman_general_prompt

    if len(chat_history) == 0 and len(summaries) == 0:
      prompt = wingman_introduction_prompt

    user_bio = {
      "full_name": "",
      "date_of_birth": "",
      "gender": "",
    }

    if user.bio_information:
      user_bio = user.bio_information.dict()
    
    chat_completion: AIMessage = openai_service.create_full_chat_completion(
      message_history=[*chat_history, new_message],
      prompt=prompt,
      additional_data={
        **user_bio, 
        "chat_context": stringify_chat_summaries(summaries) if len(summaries) > 0 else ""
      }
    )
  except Exception as e:
    print("Error at get chat response", e)
  
  return chat_completion

async def create_latest_chat_summary(
  chat_id: str, 
):
  try:
    latest_summaries = find_last_chat_summaries(chat_id=chat_id)

    last_summary = None

    if len(latest_summaries) > 0:
      last_summary = latest_summaries[0]

    messages_criteria = {}
    n_messages = None

    if last_summary:
      messages_criteria={
        "messages._id": {
          "$gte": ObjectId(last_summary["batch_id"])
        } 
      }
    else:
      n_messages = 10
    
    aggregated_chat = await get_chat_aggregated(
      chat_criteria={
        "_id": chat_id,
      },
      messages_criteria=messages_criteria,
      n_messages=n_messages
    )

    generated_summary = openai_service.generate_parsed(
      pydantic_object=ChatSummarySchema,
      prompt_template=summary_parser_prompt_template,
      additional_data={
        "chat_history": chat_stringify(aggregated_chat),
      }
    )

    summary_dict = {
      **generated_summary.dict(),
      "batch_id": str(aggregated_chat.messages[-1].id),
      "chat_id": str(aggregated_chat.id),
      "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    summary_id = vector_db.client.data_object.create(
      data_object=summary_dict, 
      class_name=ChatSummaryModel["class"]
    )
    summary = vector_db.client.data_object.get_by_id(summary_id)

    return summary
  except Exception as e:
    print("Error at create_latest_chat_summary", e)

def find_last_chat_summaries(chat_id: str):
  summaries = vector_db.client.query.get(
    ChatSummaryModel["class"],
    ["summary", "chat_id", "batch_id"]
  ).with_where({
    "path": "chat_id",
    "operator": "Equal",
    "valueText": chat_id
  }).with_sort({
    "path": ["timestamp"],
    "order": "desc"
  }).with_limit(3).do()

  return summaries["data"]["Get"][ChatSummaryModel["class"]]

def format_chat_history(chat: ChatModel, user: UserModel) -> list[AIMessage | HumanMessage]:
  formatted_chat_history = []

  for message in chat.messages:
    if message.role == "assistant":
      formatted_chat_history.append(
        AIMessage(content=message.content)
      )

      continue

    if message.role == "user":
      formatted_chat_history.append(
        HumanMessage(content=message.content)
      )

  return formatted_chat_history

def stringify_chat_summaries(chat_summaries: list[dict]) -> str:
  summary = ""

  for cs in chat_summaries:
    summary += f"\n{cs['summary']}\n"

  return summary

def chat_stringify(chat: ChatModel) -> str:
  chat_history_string = ""

  for message in chat.messages:
    role = ""

    if message.role == "assistant":
      role = "AI"
    else:
      role = "User"
    
    chat_history_string += f"{role}: {message.content}\n"

  return chat_history_string