import requests

from src.config import Config
from src.logger import get_logger

logger = get_logger(__name__)


class Notifier:
    def __init__(self, config: Config):
        self.token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.enabled = bool(self.token and self.chat_id)

    def send(self, message: str) -> None:
        if not self.enabled:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": self.chat_id, "text": message}, timeout=10)
        except requests.RequestException as exc:
            logger.warning("Failed to send Telegram notification: %s", exc)
