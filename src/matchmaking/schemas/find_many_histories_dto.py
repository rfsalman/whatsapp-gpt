
from pydantic import Field

from src.schemas.pagination import PaginationData


class FindManyHistoriesDto(PaginationData):
  success: bool = Field(default=None)
  user_id: str = Field(default=None)