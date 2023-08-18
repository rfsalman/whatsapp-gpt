
from bson import ObjectId

import src.user.service as user_service
import src.chat.service as chat_service
import src.openai_module.service as openai_service
import json
from src.databases.vector import vector_db
from src.chat.models.summary import ChatSummaryModel
from src.prompts.matchmaking import matchmaking_summary_prompt

async def start_matchmaking(user_id: str):
  try:
    user = await user_service.get_or_create_user({"_id": ObjectId(user_id)})

    if not user:
      raise Exception("User not found")
    
    user_chat = await chat_service.get_or_create_chat({
      "user":  {
        "whatsapp_id": user.whatsapp_id,
      },
    });
    
    summary_res = vector_db.client.query.get(
      ChatSummaryModel["class"],
      ["summary"]
    ).with_where({
      "path": "chat_id",
      "operator": "Equal",
      "valueText": str(user_chat.id)
    }).with_sort({
      "path": ["timestamp"],
      "order": "desc"
    }).with_limit(3).do()

    latest_summaries = summary_res["data"]["Get"][ChatSummaryModel["class"]]
    stringified_summaries = chat_service.stringify_chat_summaries(latest_summaries)

    matchmaking_summary = await openai_service.async_predict(
      prompt_template=matchmaking_summary_prompt,
      additional_data={"matchmaking_summary": stringified_summaries}
    )

    summary_matchmaking_result = vector_db.client.query.get(
      ChatSummaryModel["class"],
      ["chat_id", "summary"]
    ).with_where({
      "path": "chat_id",
      "operator": "NotEqual",
      "valueText": str(user_chat.id)
    }).with_near_text({
      "concepts": [matchmaking_summary]
    }).with_sort({
      "path": ["timestamp"],
      "order": "desc"
    }).with_limit(3).do()

    matching_summaries = summary_matchmaking_result["data"]["Get"][ChatSummaryModel["class"]]

    if len(matching_summaries) == 0:
      return
    
    matched_summary = matching_summaries[0]

    matched_user_chat = await chat_service.get_or_create_chat({
      "_id": ObjectId(matched_summary["chat_id"])
    })

    matched_user = await user_service.get_user({"phone_number": matched_user_chat.user.whatsapp_id})

    updated_user = await user_service.update_one_user(
      {"_id": user.id}, 
      {"user_match_id": matched_user.id}
    )

  except Exception as e:
    print("Error at start_matchmaking", e)