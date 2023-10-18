
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.models import PyObjectId


class ServiceUserModel(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  secret: str = Field(...)
  name: str = Field(...)
  target_name: str = Field(...)
  created_at: str | datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
  updated_at: str | datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
