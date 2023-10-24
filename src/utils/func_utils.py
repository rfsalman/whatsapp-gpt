import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

async def async_wrapper(sync_operation: Callable[..., T], *args: any, **kwargs: any) -> T:
  loop = asyncio.get_running_loop()

  func = lambda: sync_operation(*args, **kwargs)

  result = await loop.run_in_executor(None, func)
  
  return result