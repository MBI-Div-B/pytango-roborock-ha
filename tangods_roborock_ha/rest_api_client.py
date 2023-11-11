import asyncio
from typing import Any
import grequests as gr
import requests
import urllib.parse as parse


class RestAPICachingClient:
    def __init__(
        self, rest_url: str, auth_token: str, polling_period: int, entities_list: list
    ) -> None:
        self._rest_url = rest_url
        self._states_url = "{rest_url}/states/{entity_id}"
        self._services_url = "{rest_url}/services/{domain}/{service}"
        self._auth_token = auth_token
        self._get_headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        self._post_headers = {"Authorization": f"Bearer {auth_token}"}
        self._polling_period = polling_period
        self._entities_list = entities_list
        self._event_loop = asyncio.get_event_loop()
        self._event_loop.create_task(self.fetch_states())

    async def fetch_states(self):
        while True:
            state_urls = [
                self._states_url.format(rest_url = self._rest_url, entity_id = entity_id)
                for entity_id in self._entities_list
            ]
            res = (
                gr.get(
                    state_url,
                    headers=self._get_headers,
                )
                for state_url in state_urls
            )
            responses = gr.map(res)
            for response, entity_id in zip(responses, self._entities_list):
                if response is not None and response.ok:
                    setattr(self, f"{entity_id}_state", response.json())
            await asyncio.sleep(self._polling_period)

    def get_state(self, entity_id):
        return getattr(self, f"{entity_id}_state")

    def post_service(self, domain, service, json: dict):
        service_url = self._services_url.format(
            rest_url=self._rest_url, domain=domain, service=service
        )
        print(service_url)
        print(json)
        print(self._post_headers)
        res = requests.post(service_url, json=json, headers=self._post_headers)
        print(res)

    def stop_fetch(self):
        self._event_loop.stop()
