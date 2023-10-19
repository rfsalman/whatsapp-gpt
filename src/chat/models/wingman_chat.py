from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.models import PyObjectId
from src.wingman.models.wingman import WingmanAssistantModel


class WhatsappMessageMetadata(BaseModel):
  id: str = Field(default=None, description="Whatsapp Message Id")
  message_status: str = Field(default=None, description="Whatsapp Message Status")
  
class MessageModel(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  type: str = Field(alias="type", default="text")
  role: str = Field(...)
  content: str = Field(default=None)
  match_info: dict = Field(default=None)
  whatsapp_message_metadata: WhatsappMessageMetadata = Field(default=None)
  created_at: str = Field(default_factory=lambda: str(datetime.now(timezone.utc)))

class WingmanChatsModel(BaseModel):
  id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
  user_id: PyObjectId = Field(...)
  wingman_assistant_id: PyObjectId = Field(...)
  wingman_assistant: WingmanAssistantModel = Field(default=None)
  created_at: str = Field(default_factory=lambda: str(datetime.now(timezone.utc)))
  messages: list[MessageModel] = Field(default=[])