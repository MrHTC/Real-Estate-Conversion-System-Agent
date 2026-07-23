import os
import json
import time
import urllib.request
import urllib.error
from typing import Optional

from .logger import Logger


class WhatsAppSender:
    def __init__(self, api_url: str = None, api_token: str = None, retry_count: int = 3, retry_delay: int = 3):
        self.api_url = api_url or os.getenv("WHATSAPP_API_URL", "")
        self.api_token = api_token or os.getenv("WHATSAPP_API_TOKEN", "")
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.logger = Logger("WhatsApp")

    def send_message(self, phone: str, message: str) -> bool:
        if not self.api_url or not self.api_token:
            self.logger.warn("WhatsApp API details not configured. Skipping send.")
            return False

        payload = json.dumps({
            "to": phone,
            "message": message
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

        request = urllib.request.Request(self.api_url, data=payload, headers=headers, method="POST")

        for attempt in range(1, self.retry_count + 1):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status_code = getattr(response, "status", None) or response.getcode()
                    if 200 <= status_code < 300:
                        self.logger.info(f"Sent WhatsApp to {phone} (attempt {attempt})")
                        return True
                    self.logger.warn(f"WhatsApp send failed with status {status_code}")
            except urllib.error.URLError as exc:
                self.logger.warn(f"WhatsApp send attempt {attempt} failed: {exc}")
            time.sleep(self.retry_delay)

        self.logger.error(f"Failed to send WhatsApp message to {phone} after {self.retry_count} attempts")
        return False

    def send_with_retry(self, phone: str, message: str) -> bool:
        return self.send_message(phone, message)
