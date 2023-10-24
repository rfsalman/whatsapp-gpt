
from bson import ObjectId
import requests

from src.chat.models.wingman_chat import MessageModel
import src.chat.service as chat_service
import src.user.service as user_service
import src.utils.func_utils as func_utils
from src.config import config
from src.exceptions import BaseException

async def start_matchmaking(user_id: str):
  try:
    user = await user_service.get_user({"_id": ObjectId(user_id)})

    if not user:
      raise Exception("User not found")
    
  except Exception as e:
    print("Error at start_matchmaking", e)
    raise e
  
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

    # * Export chat history to discord channel
    await func_utils.async_wrapper(
      requests.post,
      url=f"{config.WINGMAN_BACKEND_API_URL}/jobs/wingman-chats-export",
      headers={
        "client-id": config.SERVICE_USER_ID,
        "client-secret": config.SERVICE_USER_SECRET
      },
      json= {
        "wingman_chat_id": str(wingman_chat.id),
        "target": "discord"
      }
    )

    return True, None
  except BaseException as e:
    print("ERROR at handle_matchmaking_start", e)
    return False, BaseException(detail={"handle_matchmaking_start": [e]})
  except Exception as e:
    print("UNEXPECTED ERROR at handle_matchmaking_start", e)
    return False, BaseException(detail={"handle_matchmaking_start": [e]})