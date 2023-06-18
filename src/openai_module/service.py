
import openai
from src.config import config
from .schemas import ChatCompletionMessageSchema, ChatCompletionOptionsSchema, ChatCompletionResponseSchema

openai.api_key = config.OPENAI_API_KEY


def create_chat_completion(messages: list[ChatCompletionMessageSchema], options: ChatCompletionOptionsSchema) -> ChatCompletionResponseSchema:
  chatCompletion = openai.ChatCompletion.create(
    messages=[message.dict() for message in messages],
    **options.dict()
  )

  return chatCompletion
