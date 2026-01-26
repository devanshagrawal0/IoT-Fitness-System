import requests
from typing import Optional


class HttpTelemetryClient:
    def __init__(self, endpoint_url: str, api_key: Optional[str] = None, timeout_s: float = 5.0):
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.timeout_s = timeout_s

    def send(self, payload: dict) -> bool:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            r = requests.post(self.endpoint_url, json=payload, headers=headers, timeout=self.timeout_s)
            return 200 <= r.status_code < 300
        except Exception:
            return False
