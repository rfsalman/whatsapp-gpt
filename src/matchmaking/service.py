
from bson import ObjectId

import src.user.service as user_service

async def start_matchmaking(user_id: str):
  try:
    user = await user_service.get_user({"_id": ObjectId(user_id)})

    if not user:
      raise Exception("User not found")
    
  except Exception as e:
    print("Error at start_matchmaking", e)
    raise e