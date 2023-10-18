from typing import Annotated
from bson import ObjectId
from fastapi import HTTPException, Header, status

import src.service_users.service as service_users_service
from src.config import config
from src.service_users.models.service_user import ServiceUserModel
from src.exceptions import (
  BaseException
)

async def authorize_service_user(
  client_id: Annotated[str | None, Header()] = None,
  client_secret: Annotated[str | None, Header()] = None,
) -> ServiceUserModel:
  try:
    if not client_id:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
          "client_id": ["Unauthorized, client_id must be provided"]
        }
      )

    if not client_secret:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
          "client_secret": ["Unauthorized, client_secret must be provided"]
        }
      )

    service_user = await service_users_service.find_one_service_user({
      "_id": ObjectId(client_id),
    })

    if not service_user or service_user.target_name != config.SERVICE_NAME:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
          "service_user": ["Forbidden access, user is not registered as this service's user"]
        }
      )

    if client_secret != service_user.secret:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
          "client_secret": ["Unauthorized, invalid credentials"]
        }
      )

    return service_user

  except BaseException as e :
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail={
        "system": ["internal system error", e]
      }
    )