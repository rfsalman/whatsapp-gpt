from pydantic import BaseModel


class PaginationData(BaseModel):
  page_number: int
  page_size: int
  sort_field: str
  sort_order: str