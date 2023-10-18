from datetime import datetime, timezone

from src.databases.mongo import db
from src.service_users.models.service_user import ServiceUserModel
from src.exceptions import (
  BaseException,
  NotFoundError
)

async def create_service_user(create_dto: ServiceUserModel) -> ServiceUserModel:
  try:
    inserted = await db["service_users"].insert_one(create_dto.dict(by_alias=True))

    service_user = await find_one_service_user({"_id": inserted.inserted_id})

    return service_user
  except Exception as e:
    raise BaseException(detail={"service_users_service.create_service_user": [e]})

async def update_one_service_user(criteria: dict, update_dto: dict, operator: dict = "$set") -> ServiceUserModel:
  try:
    service_user: ServiceUserModel = await find_one_service_user(criteria)

    if not service_user:
      criteria_error = {
        f"service_users_service.update_one_service_user": [
          f"Can't find service_user with {key}: '{criteria[key]}'"
        ] for key in criteria
      }

      raise NotFoundError(
        detail=criteria_error
      )
    
    update_data = {}

    if "secret" in update_dto:
      update_data["secret"] = update_dto["secret"]

    if "name" in update_dto:
      update_data["name"] = update_dto["name"]
    
    if "target_name" in update_dto:
      update_data["target_name"] = update_dto["target_name"]
    
    updated_at = datetime.now(timezone.utc)

    _ = await db["service_users"].update_one(
      {"_id": service_user.id},
      {
        operator: update_data,
        "$set": {"updated_at": updated_at}
      } if operator != "$set" else {"$set": {**update_data, "updated_at": updated_at}},
    )

    updated_service_user = await find_one_service_user({"_id": service_user.id})
    
    return updated_service_user
  except Exception as e:
    raise BaseException(detail={"service_users_service.update_one_service_user": [e]})

async def find_one_service_user(criteria: dict, fields: dict = None) -> ServiceUserModel | None:
  try:
    user_data = await db["service_users"].find_one(criteria, fields)

    if not user_data:
      return None

    return ServiceUserModel(**user_data)
  except Exception as e:
    raise BaseException(detail={"service_users_service.find_one_service_user": [e]})
  
async def delete_one_service_user(criteria: dict) -> None:
  try:
    _ = await db["service_users"].delete_one(criteria)

    return None
  except Exception as e:
    raise BaseException(detail={"service_users_service.delete_one_service_user": [e]})