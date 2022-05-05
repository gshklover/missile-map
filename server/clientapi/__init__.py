"""
Client-side REST API for accessing the server
"""
from typing import List

from http import HTTPStatus
import requests
import urllib.parse

from missilemap import Sighting


class ClientAPI:
    """
    Client-side python REST API for missile map server.
    Mainly used for testing the server.
    """

    def __init__(self, base_url='http://localhost:8000'):
        self._session = requests.Session()
        self._base_url = base_url

    @property
    def base_url(self) -> str:
        """
        Returns base URL for the API (http(s)://<host>:<port>/...
        """
        return self._base_url

    def add_sighting(self, sighting: Sighting) -> Sighting:
        """
        Add a sighting

        :param sighting: sighting to add
        :return:
        """
        return Sighting(**self._post('/sightings', json={
            **sighting.dict(exclude={'id'}),
            'id': str(sighting.id)
        }))

    def list_sightings(self) -> List[Sighting]:
        """
        List all sightings
        """
        return [Sighting(**d) for d in self._get('/sightings')]

    def _post(self, endpoint, json=None, params=None) -> dict:
        """
        Perform POST request to specified endpoint

        :param endpoint: relative endpoint path
        :param json: JSON data to be posted
        :param params: query parameters
        :return: result as JSON object, an exception is raised if result code is an error
        """
        url = urllib.parse.urljoin(self._base_url, endpoint)
        resp = self._session.post(url, json=json, params=params)
        if resp.status_code not in (HTTPStatus.CREATED, HTTPStatus.OK):
            raise Exception(f"Bad request status: {resp.status_code}, content: {resp.text}")
        return resp.json()

    def _get(self, endpoint, params=None) -> dict:
        """
        Perform GET request to specified endpoint

        :param endpoint: relative endpoint path
        :param params: query parameters
        :return: result as JSON object, an exception is raised if result code is an error
        """
        url = urllib.parse.urljoin(self._base_url, endpoint)
        resp = self._session.get(url, params=params)
        if resp.status_code not in (HTTPStatus.OK,):
            raise Exception(f"Bad request status: {resp.status_code}, content: {resp.text}")
        return resp.json()
