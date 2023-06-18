from src.models import PyObjectId
from src.user.models import UserModel
from src.databases.mongo import db


async def get_user(criteria: dict) -> UserModel | None:
  if "_id" in criteria:
    criteria["_id"] = PyObjectId(criteria["_id"])

  user = await db["users"].find_one(criteria)

  if not user:
    return None

  return UserModel(**user)


async def create_user(userDto: UserModel) -> UserModel:
  userData = userDto.dict()

  created = await db["users"].insert_one(userData)
  newUser = await db["users"].find_one({"_id": created.inserted_id})

  return UserModel(**newUser)


async def find_all_user(criteria: dict = {}, pagination: dict = {}) -> list[UserModel]:
  users = []

  cursor = db["users"].find(criteria)

  for userDoc in await cursor.to_list(length=None):
    users.append(UserModel(**userDoc))

  return users
