
from bson import ObjectId
import requests

from src.chat.models.wingman_chat import MessageModel
import src.chat.service as chat_service
import src.user.service as user_service
import src.utils.func_utils as func_utils
from src.config import config

async def start_matchmaking(user_id: str):
  try:
    user = await user_service.get_user({"_id": ObjectId(user_id)})

    if not user:
      raise Exception("User not found")
    
  except Exception as e:
    print("Error at start_matchmaking", e)
    raise e
  
ActionHandlerReturnType = tuple[MessageModel | None, Exception | BaseException | None]

async def handle_matchmaking_start(user_id: str, wingman_assistant_id: str):
  """
  Action Handler to initiate Matchmaking
  Returns the status of the action handler (AI Message or null), and an exception, if any
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
      json= {
        "wingman_chat_id": str(wingman_chat.id),
        "target": "discord"
      }
    )
    
    # * Initiate matchmaking
    await start_matchmaking(user_id)

    return None, None
  except BaseException as e:
    print("ERROR at handle_matchmaking_start", e)
    return False, BaseException(detail={"handle_matchmaking_start": [e]})
  except Exception as e:
    print("UNEXPECTED ERROR at handle_matchmaking_start", e)
    return False, BaseException(detail={"handle_matchmaking_start": [e]})