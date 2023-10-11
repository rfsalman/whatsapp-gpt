import weaviate
from weaviate import exceptions
from fastapi import status

from src.config import config
from src.helpers.topics import MessageTopics
from src.chat.models.topics import TopicModel
from src.chat.models.summary import ChatSummaryModel


class VectorDB():
  client: weaviate.Client = None

  def init(self):
    self.client = weaviate.Client(
      url=config.WEAVIATE_URL,
      auth_client_secret=weaviate.auth.AuthApiKey(config.WEAVIATE_API_KEY),
      additional_headers={
        "X-OpenAI-API-Key": config.OPENAI_API_KEY,
        "X-Cohere-Api-Key": config.COHERE_API_KEY
      }
    )

    try:
      _ = self.client.schema.get(ChatSummaryModel["class"])
    except exceptions.UnexpectedStatusCodeException as e:
      if e.status_code == status.HTTP_404_NOT_FOUND:
        self.client.schema.create_class(ChatSummaryModel)
      
vector_db = VectorDB()