from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field

from src.storage.models.file import FileModel
from src.models import PyObjectId
from src.wingman.models.wingman import WingmanAssistantModel

class PushNotificationConfig(BaseModel):
  type: str = Field(default=None)
  token: str = Field(default=None)

class UserBioModel(BaseModel):
  full_name: str = Field(default=None)
  date_of_birth: str = Field(default=None)
  pictures: list[FileModel] = Field(default=[])
  relationship_goal: str = Field(default=None)
  interests: list[str] = Field(default=[])
  gender: str = Field(default=None)
  matchmaking_summary: str = Field(default=None)

class UserModel(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  email: str  = Field(default=None)
  phone_number: str = Field(default=None)
  password: str = Field(default=None)
  bio: UserBioModel = Field(default=None)
  source: str = Field(default="whatsapp")
  verified: bool = Field(default=False)
  verification_request_id: PyObjectId = Field(default=None)
  change_password_request_id: PyObjectId = Field(default=None)
  selected_wingman_id: PyObjectId = Field(default=None)
  selected_wingman: WingmanAssistantModel = Field(default=None)
  potential_matches: list[dict] = Field(default=[]) # ? PotentialMatchModel
  push_notification_config: PushNotificationConfig = Field(default=None)
  created_at: str = Field(default_factory=lambda: str(datetime.now(timezone.utc)))
  updated_at: str = Field(default_factory=lambda: str(datetime.now(timezone.utc)))

  class Config:
    allow_population_by_field_name = True
    json_encoders = {ObjectId: str}
    schema_extra = {
      "example": {
        "_id": "64a18d4b2dc595551aaea80b",
        "email": "dennis_ritchie@gmail.com",
        "password": "12345",
        "bio": {
          "full_name": "Dennis Ritchie",
          "date_of_birth": "",
          "gender": "male",
          "pictures": [
            {
              "_id": "64a18d4b2dc595551aaea80b",
              "path": "pictures/users/64a18d4b2dc595551aaea80b/64a18d4b2dc595551aaea80b.jpg",
              "filename": "64a18d4b2dc595551aaea80b.jpg",
              "original_filename": "my-picture.jpg",
              "size": 128328,
              "url": "https://storage.googleapis.com/ai-wingman.appspot.com/pictures/users/64a21e7e94ec255ffbc4bf7f.jpeg",
            }
          ],
          "relationship_goal": "",
          "interests": ["technology", "books", "gaming"]
          },
        "verified": False,
        "verification_request_id": None,
        "change_password_request_id": None,
        "created_at": "2023-07-04T13:57:50.182764+00:00",
        "updated_at": "2023-07-04T13:57:50.182764+00:00"
      }
    }