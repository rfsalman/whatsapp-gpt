
import asyncio
from datetime import datetime, timezone
from bson import ObjectId
from langchain.schema import (
  AIMessage,
  BaseMessage,
  HumanMessage
)

import src.user.service as user_service
import src.wingman.service as wingman_service
import src.openai_module.service as openai_service
import src.helpers.string_helpers as string_helpers
import src.matchmaking.service as matchmaking_service
from src.chat.models.summary import ChatSummaryModel
from src.chat.schemas.summary import ChatSummarySchema
from src.databases.mongo import db
from src.wingman.models.wingman import WingmanAssistantModel
from .models.wingman_chat import WingmanChatsModel, MessageModel
from src.user.models.user import UserModel
from src.whatsapp_webhook.schemas.webhook_payload_schema import (
  WaMessage,
  WaContact,
)
from src.databases.vector import vector_db
from src.utils.dict import flatten_dict
from src.helpers.action_triggers import ActionTriggers
from src.prompts.chat_summary import summary_parser_prompt_template
from src.prompts.wingman import (
  wingman_introduction_prompt,
  wingman_general_prompt,
)

async def get_or_create_chat(chat_criteria: dict) -> WingmanChatsModel:
  try:
    chat = await find_one_chat(chat_criteria, {"messages": 0})

    if not chat:
      # ? Get random wingman asisstant's id
      wingman_assistant_id = chat_criteria["wingman_assistant_id"] if "wingman_assistant_id" in chat_criteria else None

      if not wingman_assistant_id:
        wingman_assistant = await wingman_service.find_one_wingman({})
        wingman_assistant_id = wingman_assistant.id

      chat_criteria["wingman_assistant_id"] = wingman_assistant_id
      
      chat = await create_chat(WingmanChatsModel(**chat_criteria))
      
    return chat
  except Exception as e:
    raise e  

async def create_chat(chat_dto: WingmanChatsModel) -> WingmanChatsModel:
  try:
    inserted = await db["wingman_chats"].insert_one(chat_dto.dict(by_alias=True))

    chat = await find_one_chat({"_id": inserted.inserted_id}, {"messages": 0})

    return chat
  except Exception as e:
    print("Error at create_chat", e)
    
    raise e

async def find_one_chat(chat_crit: dict, fields: dict = None):
  try:
    chat_crit = flatten_dict(chat_crit)
    chat_data = await db["wingman_chats"].find_one(chat_crit, fields)

    if not chat_data:
      return None

    return WingmanChatsModel(**chat_data)
  except Exception as e:
    raise e

async def get_chat_aggregated(
  chat_criteria: dict, 
  messages_criteria: dict, 
  n_messages: int
) -> WingmanChatsModel | None:
  try:
    chat_criteria = flatten_dict(chat_criteria)

    pipeline = [
      stage for stage in [
        {"$match": chat_criteria},
        {"$unwind": {"path": "$messages", "preserveNullAndEmptyArrays": True}},
        {"$match": messages_criteria} if messages_criteria else None,
        {"$sort": {"messages.created_at": -1}},
        {"$limit": n_messages} if isinstance(n_messages, int) and isinstance(n_messages, int) else None,
        {"$group": {
          "_id": "$_id",
          "user_id": { "$first": "$user_id" },
          "wingman_assistant_id": { "$first": "$wingman_assistant_id" },
          "created_at": { "$first": "$created_at" },
          "messages": {"$push": "$messages"}
        }}
      ] if stage is not None
    ]

    chat = await db["wingman_chats"].aggregate(pipeline).to_list(length=1)

    if chat:
      chat = WingmanChatsModel(**(chat[0]))

      chat.messages = chat.messages[::-1] if chat.messages else []
            
      return chat

    return None
  except Exception as e:
    print("Error at get_chat_aggregated", e)
    
    raise e

async def upsert_chat_message(chat_data: dict, messages: list[MessageModel]) -> WingmanChatsModel | None:
  update = {
    "$push": {
      "messages": {
        "$each": [{
          "_id": message.id,
          "type": message.type,
          "content": message.content,
          "role": message.role,
          "created_at": message.created_at,
          "whatsapp_message_metadata": 
            message.whatsapp_message_metadata.dict(by_alias=True) 
            if message.whatsapp_message_metadata else None
        } for message in messages]
      }
    }
  }

  if len(messages) > 0:
    update["$set"] = {
      "last_message_at": datetime.now(timezone.utc)
    }
  
  _ = await db["wingman_chats"].update_one(
    chat_data,
    update,
    upsert=True
  )

  chat = await find_one_chat(chat_data, {"messages": 0})

  if not chat:
    return None

  return chat

async def handle_chat_message_pipeline(
  message: WaMessage, 
  contact: WaContact,
) -> tuple[WingmanChatsModel, AIMessage, list[BaseMessage]]:
  try:
    # * Get/Create user
    user = await user_service.get_or_create_user(
      {
        "phone_number": contact.wa_id
      }
    )

    # * Get/Create chat
    user_chat = await get_or_create_chat(
      {
        "user_id": user.id,
        "wingman_assistant_id": user.selected_wingman_id
      }
    )

    summaries = find_last_chat_summaries({
      "path": "user_id",
      "operator": "Equal",
      "valueText": str(user.id)
    })

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
          "$gte": ObjectId(last_summary["last_message_id"])
        } 
      } if last_summary else {},
      n_messages=10
    )

    # * Chat doesn't have any summary or can't find last_message
    if not aggregated_chat:
      aggregated_chat = await get_chat_aggregated(
      chat_criteria={
        "_id": user_chat.id,
      },
      messages_criteria=None,
      n_messages=10
    )

    if not aggregated_chat:
      return (None, None, None)
    
    wingman_assistant = await wingman_service.find_one_wingman({"_id": aggregated_chat.wingman_assistant_id})

    # * Format chat history into langchain chat prompt
    chat_history = format_chat_history(aggregated_chat, user)
    new_message = HumanMessage(content=message.text.body)
    
    # * Get Chat Response
    chat_completion: AIMessage = await get_chat_response(
      wingman_assistant=wingman_assistant,
      chat_history=chat_history,
      new_message=new_message,
      user=user,
      summaries=summaries
    )

    return (aggregated_chat, chat_completion, chat_history)
    
  except Exception as e:
    print("Error at handle msg pipeline", e)
    
    raise e
  
async def get_chat_response(
  wingman_assistant: WingmanAssistantModel,
  chat_history: list[AIMessage | HumanMessage],
  new_message: AIMessage | HumanMessage, 
  user: UserModel,
  summaries: list[dict] = [],
) -> AIMessage:
  try:
    prompt = wingman_general_prompt

    # ? Use introduction prompt for new user
    if len(chat_history) == 0 and len(summaries) == 0:
      prompt = wingman_introduction_prompt

    chat_completion: AIMessage = await openai_service.create_full_chat_completion(
      message_history=[*chat_history, new_message],
      prompt=prompt,
      additional_data={
        "wingman_name": wingman_assistant.name,
        "wingman_title": wingman_assistant.title,
        "wingman_personality": wingman_assistant.description,
        "chat_context": stringify_chat_summaries(summaries) if len(summaries) > 0 else "",
      }
    )

    actions, new_message_content = string_helpers.get_string_and_remove_enum_flags(chat_completion.content, ActionTriggers)

    if len(actions) > 0:
      if actions[0] == ActionTriggers.MATCHMAKING_START:
        asyncio.create_task(matchmaking_service.start_matchmaking(user_id=user.id))

    chat_completion.content = new_message_content

  except Exception as e:
    print("Error at get chat response", e)
  
  return chat_completion

async def create_latest_chat_summary(
  wingman_chat_id: str, 
):
  try:
    latest_summaries = find_last_chat_summaries({
      "path": "chat_id",
      "operator": "Equal",
      "valueText": wingman_chat_id
    })

    last_summary = None

    if len(latest_summaries) > 0:
      last_summary = latest_summaries[0]

    messages_criteria = {}
    n_messages = None

    if last_summary:
      messages_criteria={
        "messages._id": {
          "$gte": ObjectId(last_summary["last_message_id"])
        } 
      }
    else:
      n_messages = 10
    
    aggregated_chat = await get_chat_aggregated(
      chat_criteria={
        "_id": ObjectId(wingman_chat_id),
      },
      messages_criteria=messages_criteria,
      n_messages=n_messages
    )

    if not aggregated_chat:
      aggregated_chat = await get_chat_aggregated(
      chat_criteria={
        "_id": ObjectId(wingman_chat_id),
      },
      messages_criteria=None,
      n_messages=10
    )

    generated_summary = openai_service.generate_parsed(
      pydantic_object=ChatSummarySchema,
      prompt_template=summary_parser_prompt_template,
      additional_data={
        "chat_history": chat_stringify(aggregated_chat),
      }
    )

    summary_dict = {
      "topics": generated_summary.topics[:4] if isinstance(generated_summary.topics, list) else [],
      "summary": generated_summary.summary,
      "user_id": str(aggregated_chat.user_id),
      "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
      "last_message_id": str(aggregated_chat.messages[-1].id),
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

def find_last_chat_summaries(
  criterias: dict = None,
  sort: dict = {
    "path": ["timestamp"],
    "order": "desc"
  }
):
  result = None

  query = vector_db.client.query.get(
    ChatSummaryModel["class"],
    ["summary", "chat_id", "last_message_id", "topics"]
  ).with_sort(sort).with_limit(4)

  if criterias:
    query.with_where(criterias)

  result = query.do()

  summaries = result["data"]["Get"][ChatSummaryModel["class"]] if result else []

  return summaries

def format_chat_history(chat: WingmanChatsModel, user: UserModel) -> list[AIMessage | HumanMessage]:
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
    summary += f"\nTopic: {cs['topics']}\n{cs['summary']}\n"

  return summary

def chat_stringify(chat: WingmanChatsModel) -> str:
  chat_history_string = ""

  for message in chat.messages:
    role = ""

    if message.role == "assistant":
      role = "AI"
    else:
      role = "User"
    
    chat_history_string += f"{role}: {message.content}\n"

  return chat_history_string