
from fastapi import FastAPI

from ep_api_openclaw.router import router
from ep_api_openclaw.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix=settings.api_prefix)
