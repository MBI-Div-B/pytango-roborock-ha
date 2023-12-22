import asyncio
from typing import Any
import grequests as gr
import requests
import urllib.parse as parse


class RestAPICachingClient:
    def __init__(self, rest_url: str, auth_token: str, entities_list: list) -> None:
        self._rest_url = rest_url
        self._states_url = "{rest_url}/states/{entity_id}"
        self._services_url = "{rest_url}/services/{domain}/{service}"
        self._auth_token = auth_token
        self._get_headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        self._post_headers = {"Authorization": f"Bearer {auth_token}"}
        self._entities_list = entities_list

    def fetch_states(self):
        state_urls = [
            self._states_url.format(rest_url=self._rest_url, entity_id=entity_id)
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

    def get_state(self, entity_id):
        return getattr(self, f"{entity_id}_state")

    def post_service(self, domain, service, json: dict):
        service_url = self._services_url.format(
            rest_url=self._rest_url, domain=domain, service=service
        )
        res = requests.post(service_url, json=json, headers=self._post_headers)
