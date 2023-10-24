
import uvicorn
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.wingman_api_client import WingmanAPIClient
from src.whatsapp_api_client import WhatsappAPIClient
from src.config import config
from src.databases.vector import vector_db
from src.whatsapp_webhook.router import router as wa_webhook_router

@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
  WingmanAPIClient.init_session()
  WhatsappAPIClient.init_session()
  
  vector_db.init()
  
  yield

  wingman_session = WingmanAPIClient.get_session()
  whatsapp_session = WhatsappAPIClient.get_session()

  wingman_session.close()
  whatsapp_session.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
  CORSMiddleware
)

@app.get("/healthcheck", include_in_schema=False)
async def healthcheck():
  return {"status": "ok"}

app.include_router(wa_webhook_router, prefix="/whatsapp", tags=["whatsapp-webhook"])

@app.get("/")
def read_root():
  return {"Hello": "World"}

if __name__ == "__main__":
  port = int(config.PORT)  # default port is 8000 if PORT env var is not set
  env = config.ENV  # default to PROD if ENV var is not set

  if env == "DEV":
    uvicorn.run(app, host="0.0.0.0", port=port)
  else:
    uvicorn.run(app, host="0.0.0.0", port=port)

