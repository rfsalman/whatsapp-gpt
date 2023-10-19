
from pydantic import BaseModel, Field

class UserActivationMessageDto(BaseModel):
  activation_link_query_string: str = Field(...)
  message_template: str = Field(...)
  user_id: str = Field(...)
  