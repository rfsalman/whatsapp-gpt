from pydantic import BaseSettings

class Config(BaseSettings):
  MONGODB_URI: str
  MONGO_INITDB_DATABASE: str
  WHATSAPP_WEBHOOK_VERIFY_TOKEN: str
  OPENAI_API_KEY: str
  OPENAI_CHAT_MAX_TOKEN: int
  FACEBOOK_API_URL: str
  FACEBOOK_APP_SECRET: str
  WHATSAPP_ACCESS_TOKEN: str
  ADMIN_JWT_SECRET: str
  JWT_ALGORITHM: str
  ENV: str
  PORT: int
  WEAVIATE_URL: str
  WEAVIATE_API_KEY: str
  COHERE_API_KEY: str
  SERVICE_NAME: str
  SERVICE_USER_ID: str
  SERVICE_USER_SECRET: str
  WINGMAN_BACKEND_API_URL: str
  
  class Config:
    env_file = "./src/.env"

config = Config()