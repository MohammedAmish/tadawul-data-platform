from __future__ import annotations

import json


class TadawulActions:

    def __init__(self, driver):
        self.driver = driver

    def fetch(self, action: str, params: dict[str, str]):
        query = "&".join(
            f"{key}={self._encode(value)}"
            for key, value in params.items()
        )

        script = """
        const done = arguments[arguments.length - 1];

        const action = arguments[0];
        const query = arguments[1];

        /*
         * We use the current portal origin and current page context.
         * The browser already owns the WebSphere session.
         */

        const url =
            window.location.origin +
            window.location.pathname +
            action +
            "/?" +
            query;

        fetch(url, {
            method: "GET",
            credentials: "include",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(async response => {
            const text = await response.text();

            done({
                ok: response.ok,
                status: response.status,
                url: response.url,
                body: text
            });
        })
        .catch(error => {
            done({
                ok: false,
                error: String(error)
            });
        });
        """

        return self.driver.execute_async_script(
            script,
            action,
            query,
        )

    @staticmethod
    def _encode(value):
        import urllib.parse

        return urllib.parse.quote(
            str(value),
            safe=""
        )