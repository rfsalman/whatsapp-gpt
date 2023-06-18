from pydantic import BaseModel, Field
from bson import ObjectId
from src.models import PyObjectId


class UserModel(BaseModel):
  _id: PyObjectId = Field(default_factory=PyObjectId)
  phone_number: str = Field(default="")
  whatsapp_id: str = Field(default="")
  name: str = Field(default="")

  class Config:
    allow_population_by_field_name = True
    arbitrary_types_allowed = True
    json_encoders = {ObjectId: str}
    schema_extra = {
      "example": {
        "id": "60d5e1d636b7b9f9a9b9b8d7",
        "full_name": "Salman Rizqi Fatih",
        "phone_number": "628976664322",
      }
    }

  def fromDict(userDict: dict):
    return UserModel.parse_obj(userDict)
