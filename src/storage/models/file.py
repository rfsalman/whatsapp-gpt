from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field

from src.models import PyObjectId

class FileModel(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  path: str = Field(...)
  filename: str = Field(...)
  original_filename: str = Field(...)
  size: int = Field(...)
  url: str = Field(...)
  created_at: str = Field(default_factory=lambda: str(datetime.now(timezone.utc)))

  class Config:
    allow_population_by_field_name = True
    json_encoders = {ObjectId: str}
    schema_extra = {
      "example": {
        "_id": "64a18d4b2dc595551aaea80b",
        "path": "pictures/users/64a18d4b2dc595551aaea80b/64a18d4b2dc595551aaea80b.jpg",
        "filename": "64a18d4b2dc595551aaea80b.jpg",
        "original_filename": "my-picture.jpg",
        "size": 128328,
        "url": "https://storage.googleapis.com/ai-wingman.appspot.com/pictures/users/64a21e7e94ec255ffbc4bf7f.jpeg"
      }
    }