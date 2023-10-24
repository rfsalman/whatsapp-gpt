
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.models import PyObjectId

class MatchmakingResult(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  user_id: PyObjectId = Field(...)
  matchmaking_summary: str = Field(default=None)

class MatchmakingHistoryModel(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  user_id: PyObjectId = Field(...)
  success: bool = Field(default=False)
  matchmaking_summary: str = Field(default=None)
  matchmaking_results: list[MatchmakingResult] = Field(default=[])
  created_at: str | datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
  updated_at: str | datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
  