from aiohttp import ClientSession

from src.config import config

class WingmanAPIClient:
  _session: ClientSession = None

  @classmethod
  def init_session(cls):
    headers = {
        "client-id": config.SERVICE_USER_ID,
        "client-secret": config.SERVICE_USER_SECRET,
      }
      
    cls._session = ClientSession(headers=headers)

  @classmethod
  def get_session(cls) -> ClientSession:
    return cls._session
