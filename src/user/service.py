from src.models import PyObjectId
from src.user.models import UserModel
from src.databases.mongo import db
from src.utils.dict import flatten_dict

async def get_user(criteria: dict) -> UserModel | None:
  if "_id" in criteria:
    criteria["_id"] = PyObjectId(criteria["_id"])

  user = await db["users"].find_one(criteria)

  if not user:
    return None

  return UserModel(**user)


async def create_user(user_dto: dict) -> UserModel:
  userData = user_dto

  created = await db["users"].insert_one(userData)

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

async def update_one_user(criteria: dict = {}, update_dto: dict = {}) -> UserModel | None:
  user = await get_user(flatten_dict(criteria=criteria))

  if not user:
    return None
  
  _ = await db["users"].update_one(criteria, {"$set": update_dto})

  user = await get_user(flatten_dict(criteria=criteria))

  return user
