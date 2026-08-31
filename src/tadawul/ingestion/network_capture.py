from __future__ import annotations

import json
import time
from typing import Any


class NetworkCapture:
    def __init__(self, driver):
        self.driver = driver
        self.requests: dict[str, dict[str, Any]] = {}

    def collect(self, wait_seconds: float = 3):
        time.sleep(wait_seconds)

        logs = self.driver.get_log("performance")

        for entry in logs:
            message = json.loads(entry["message"])["message"]

            method = message.get("method")
            params = message.get("params", {})

            if method == "Network.responseReceived":
                response = params.get("response", {})
                request_id = params.get("requestId")

                if not request_id:
                    continue

                url = response.get("url", "")

                self.requests[request_id] = {
                    "request_id": request_id,
                    "url": url,
                    "status": response.get("status"),
                    "mime_type": response.get("mimeType"),
                    "headers": response.get("headers", {}),
                    "body": None,
                }

            elif method == "Network.loadingFinished":
                request_id = params.get("requestId")

                if request_id in self.requests:
                    self._get_body(request_id)

        return list(self.requests.values())

    def _get_body(self, request_id: str):
        try:
            result = self.driver.execute_cdp_cmd(
                "Network.getResponseBody",
                {
                    "requestId": request_id,
                },
            )

            self.requests[request_id]["body"] = result.get("body")

        except Exception as exc:
            self.requests[request_id]["body_error"] = str(exc)

    def find(self, text: str):
        return [
            request
            for request in self.requests.values()
            if text.lower() in request["url"].lower()
        ]