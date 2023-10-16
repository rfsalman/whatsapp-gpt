
from src.exceptions import InternalServerError
from src.databases.mongo import db
from src.wingman.models.wingman import WingmanAssistantModel


async def find_one_wingman(criteria: dict) -> WingmanAssistantModel:
  try:
    wingman_assistant = await db["wingman_assistants"].find_one(criteria)

    if not wingman_assistant:
      return None

    return WingmanAssistantModel(**wingman_assistant)
  except Exception as e:
    print(e, ' <<< e find_one_wingman')
    raise InternalServerError(detail={
      "system": ["Internal server error"]
    })