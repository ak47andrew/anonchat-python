from anonchat import config
from typing import Any


def uri_auth(uri: str) -> dict[str, str]:
    if not uri.startswith("ws://") and not uri.startswith("wss://"):
        raise ValueError("Invalid WebSocket URI")
    if "?" not in uri:
        raise ValueError("No query string provided")

    query_string = uri.split('?')[1]

    params = {k: v for k, v in (p.split("=") for p in query_string.split("&"))}
    if "cookie" not in params or "secret" not in params:
        raise ValueError("Missing required query parameters: cookie, secret")

    return {
        "cookie": params["cookie"],
        "secret": params["secret"]
    }


def generate_data() -> dict[str, Any]:
    import locale
    import platform
    import uuid
    lang = locale.getlocale()[0]

    return {
        "version": config.APP_VERSION,
        "systemLanguage": lang.split("_")[0],
        "systemRawLanguage": lang,
        "platform": platform.system().lower(),
        "systemInfo": platform.platform(),
        "isEmulator": False,
        "admin": None,
        "deviceId": uuid.uuid4().hex[:16],
        "cookie": None,
        "secret": None,
        "EIO": 4,
        "transport": "websocket"
    }
