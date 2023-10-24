
from pydantic import BaseModel, Field


class CreateUserVerificationTokenDto(BaseModel):
  user_id: str
  expired_in: int = Field(default=None)

class CreateUserVerificationTokenResult(BaseModel):
  verification_request_token: str
  user_id: str
  expired_in: int 