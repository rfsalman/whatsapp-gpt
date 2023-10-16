from pydantic import BaseModel, Field

from src.models import PyObjectId
from src.storage.models.file import FileModel


class WingmanAssistantModel(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  name: str
  title: str
  description: str
  picture: FileModel = Field(default=None)
