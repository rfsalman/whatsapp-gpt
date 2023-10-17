import weaviate
from weaviate import exceptions
from fastapi import status

from src.config import config

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
      
vector_db = VectorDB()