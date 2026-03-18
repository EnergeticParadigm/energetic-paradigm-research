
import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_prefix: str
    hmac_client_id: str
    hmac_secret: str
    bearer_token: str
    allowed_clock_skew_seconds: int
    nonce_ttl_seconds: int
    nonce_db_path: str
    ep_engine_base_url: str
    ep_engine_timeout_seconds: float
    ep_engine_query_handler: str
    ep_engine_compare_handler: str

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            app_name=os.getenv("EP_OPENCLAW_APP_NAME", "EP OpenClaw Bridge"),
            api_prefix=os.getenv("EP_OPENCLAW_API_PREFIX", "/v1"),
            hmac_client_id=os.getenv("EP_OPENCLAW_HMAC_CLIENT_ID", "openclaw-prod"),
            hmac_secret=os.getenv("EP_OPENCLAW_HMAC_SECRET", "CHANGE_ME"),
            bearer_token=os.getenv("EP_OPENCLAW_BEARER_TOKEN", ""),
            allowed_clock_skew_seconds=int(os.getenv("EP_OPENCLAW_ALLOWED_CLOCK_SKEW_SECONDS", "300")),
            nonce_ttl_seconds=int(os.getenv("EP_OPENCLAW_NONCE_TTL_SECONDS", "600")),
            nonce_db_path=os.getenv(
                "EP_OPENCLAW_NONCE_DB_PATH",
                "/Users/wesleyshu/ep_system/ep_api_system/ep_api_openclaw/nonces.sqlite3",
            ),
            ep_engine_base_url=os.getenv("EP_ENGINE_BASE_URL", ""),
            ep_engine_timeout_seconds=float(os.getenv("EP_ENGINE_TIMEOUT_SECONDS", "120")),
            ep_engine_query_handler=os.getenv(
                "EP_ENGINE_QUERY_HANDLER",
                "ep_api_openclaw.example_engine_handlers:example_query_handler",
            ),
            ep_engine_compare_handler=os.getenv(
                "EP_ENGINE_COMPARE_HANDLER",
                "ep_api_openclaw.example_engine_handlers:example_compare_handler",
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.load()
