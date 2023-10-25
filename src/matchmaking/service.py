
from bson import ObjectId
from fastapi import HTTPException, status

import src.chat.service as chat_service
from src.config import config
from src.wingman_api_client import WingmanAPIClient
from src.exceptions import BaseException
from src.wingman_api_client import WingmanAPIClient
from src.config import config
from src.schemas.api_response import ApiResponse
from src.matchmaking.models.matchmaking_history import MatchmakingHistoryModel
from src.matchmaking.schemas.find_many_histories_dto import FindManyHistoriesDto

ActionHandlerReturnType = tuple[bool, Exception | BaseException | None]

async def handle_matchmaking_start(user_id: str, wingman_assistant_id: str) -> ActionHandlerReturnType:
  """
  Action Handler to initiate Matchmaking
  Returns the boolean status of the action handler (True or False), and an exception, if any
  """
  try:
    wingman_chat = await chat_service.find_one_chat({
      "user_id": ObjectId(user_id),
      "wingman_assistant_id": ObjectId(wingman_assistant_id)
    })

    session = WingmanAPIClient.get_session()

    chat_exports_job_url = f"{config.WINGMAN_BACKEND_API_URL}/jobs/wingman-chats-export"
    init_matchmaking_job_url = f"{config.WINGMAN_BACKEND_API_URL}/jobs/matchmaking"

    # * Export chat history to discord channel
    async with session.post(
      chat_exports_job_url,
      json={
        "wingman_chat_id": str(wingman_chat.id),
        "target": "discord"
      }
    ) as export_res:
      export_res_json = await export_res.json()
    
    if export_res.status != status.HTTP_200_OK:
      raise HTTPException(
        status_code=export_res.status,
        detail=export_res_json["errors"] if "errors" in export_res_json else export_res_json
      )
    
    # * Initiate matchmaking
    async with session.post(
      init_matchmaking_job_url,
      json={
        "user_id": user_id
      }
    ) as init_matchmaking_res:
      init_matchmaking_res_json = await init_matchmaking_res.json()

    if init_matchmaking_res.status != status.HTTP_200_OK:
      raise HTTPException(
        status_code=init_matchmaking_res.status,
        detail=init_matchmaking_res_json["errors"] if "errors" in init_matchmaking_res_json else init_matchmaking_res_json
      )
    
    return True, None
  except HTTPException as e:
    print("HTTP ERROR at handle_matchmaking_start", e)

    return False, e
    
  except BaseException as e:
    print("ERROR at handle_matchmaking_start", e)
    return False, BaseException(detail={"handle_matchmaking_start": [e]})
  except Exception as e:
    print("UNEXPECTED ERROR at handle_matchmaking_start", e)
    return False, BaseException(detail={"handle_matchmaking_start": [e]})
  
async def find_many_matchmaking_histories(find_dto: FindManyHistoriesDto) -> list[MatchmakingHistoryModel]:
  try:
    matchmaking_api_url = f"{config.WINGMAN_BACKEND_API_URL}/api/matchmaking/histories"
    params = {key: val for key, val in find_dto.dict().items() if val != None}

    session = WingmanAPIClient.get_session()

    async with session.get(
      matchmaking_api_url,
      params=params
    ) as response:
      json_response = await response.json() 
      response_data = ApiResponse[list[MatchmakingHistoryModel]](**json_response)

      if response.status != status.HTTP_200_OK:
        raise HTTPException(
          status_code=response.status,
          detail=json_response["errors"] if "errors" in json_response else json_response
        )
    
    return response_data.data
  except HTTPException as e:
    raise e
    
  except Exception as e:
    print("EXCEPTION at find_many_matchmaking_histories", e)
    
    raise BaseException(
      detail={
        "find_many_matchmaking_histories": [str(e)]
      }
    )
