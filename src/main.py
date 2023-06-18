
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.whatsapp_webhook.router import router as wa_webhook_router

@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
  yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
  CORSMiddleware
)

@app.get("/healthcheck", include_in_schema=False)
async def healthcheck():
  return {"status": "ok"}

app.include_router(wa_webhook_router, prefix="/webhooks/whatsapp", tags=["whatsapp-webhook"])



