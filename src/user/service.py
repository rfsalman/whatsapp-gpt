
from fastapi import status, HTTPException

import src.wingman.service as wingman_service
from src.wingman_api_client import WingmanAPIClient
from src.config import config
from src.user.models.user import UserModel
from src.user.schemas.create_user_verification_token import (
  CreateUserVerificationTokenDto,
  CreateUserVerificationTokenResult
)
from src.databases.mongo import db
from src.utils.dict import flatten_dict
from src.exceptions import (
  BaseException
)

async def get_user(criteria: dict) -> UserModel | None:
  user = await db["users"].find_one(criteria)

  if not user:
    return None

  return UserModel(**user)

async def create_user(user_dto: dict) -> UserModel:
  userData = user_dto

  selected_wingman = await wingman_service.find_one_wingman({})

  if selected_wingman:
    userData["selected_wingman_id"] = selected_wingman.id

  created = await db["users"].insert_one(UserModel(**userData).dict(by_alias=True))

  newUser = await db["users"].find_one({"_id": created.inserted_id})

  return UserModel(**newUser)

async def get_or_create_user(user_dto: UserModel) -> UserModel:
  user_criteria = flatten_dict(user_dto)

  user = await get_user(user_criteria)

  if not user:
    user = await create_user(user_dto)

  return user

async def find_all_user(criteria: dict = {}, pagination: dict = {}) -> list[UserModel]:
  users = []

  cursor = db["users"].find(criteria)

  for userDoc in await cursor.to_list(length=None):
    users.append(UserModel(**userDoc))

  return users

async def update_one_user(criteria: dict = {}, update_dto: dict = {}, operator = "$set") -> UserModel | None:
  user = await get_user(flatten_dict(criteria=criteria))

  if not user:
    return None
  
  _ = await db["users"].update_one(criteria, {operator: update_dto})

  user = await get_user(flatten_dict(criteria=criteria))

  return user

async def create_user_verification_token(user_id: str) -> CreateUserVerificationTokenResult:
  try:
    session = WingmanAPIClient.get_session()
    
    user_verification_token_url = f"{config.WINGMAN_BACKEND_API_URL}/jobs/user-verification-token"

    dto = CreateUserVerificationTokenDto(
      user_id=user_id
    )

    payload = {key: val for key, val in dto.dict().items() if val}

    async with session.post(
      user_verification_token_url,
      json=payload
    ) as response:
      print("response", response)
      json_response = await response.json()

      if response.status != status.HTTP_200_OK:        
        raise HTTPException(
          status_code=response.status,
          detail=json_response["errors"] if "errors" in json_response else json_response
        )
      
    response_data = CreateUserVerificationTokenResult(
      **json_response["data"]
    )
    
    return response_data
  except HTTPException as e:
    print("HTTPException at create_user_verification_token", e)
    
    raise e
  
  except BaseException as e:
    print("BaseException at create_user_verification_token", e)
    
    raise e
    
  except Exception as e:
    print("Exception at create_user_verification_token", e)
    
    raise BaseException(
      detail={
        "create_user_verification_token": [str(e)]
      }
    )
