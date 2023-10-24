from aiohttp import ClientSession

from src.config import config

class WhatsappAPIClient:
  _session: ClientSession = None

  @classmethod
  def init_session(cls):
    headers = {
      "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
      "Content-Type": "application/json"
    }
      
    cls._session = ClientSession(headers=headers)

  @classmethod
  def get_session(cls) -> ClientSession:
    return cls._session
