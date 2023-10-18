from typing import Generic, TypeVar
from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

M = TypeVar("M", bound=BaseModel)

class ApiResponse(GenericModel, Generic[M]):
  code: int = Field(default=200)
  status: str = Field(default="success")
  data: M = Field(default=None)
  message: str = Field(default=None)

  class Config:
    allow_population_by_field_name = True
    json_encoders = {ObjectId: str}
    
class ApiErrorResponse(BaseModel):
  code: int
  status: str
  errors: dict

  class Config:
    allow_population_by_field_name = True
    json_encoders = {ObjectId: str}

    schema_extra = {
      "example": {
        "code": 404,
        "status": "error",
        "errors": {
          "field": ["Error message"]
        }
      }
    }
