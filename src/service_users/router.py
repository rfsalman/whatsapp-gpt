
from typing import Annotated
from fastapi import APIRouter, Depends

from src.schemas.api_response import ApiResponse
from src.service_users.models.service_user import ServiceUserModel
from src.service_users.dependencies.authorization import authorize_service_user

service_user_router = APIRouter()

@service_user_router.get(
  "/test",
  responses={
    200: {"model": ApiResponse[str]},
  }
)
async def test_route(
  _: Annotated[ServiceUserModel, Depends(authorize_service_user)],
):
  return ApiResponse[str](data="OK")