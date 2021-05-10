import aiohttp

from bot.utils import constants


class ResponseStatusCodeException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):
        return f"ResponseStatusCodeException: {self.code}: {self.message}"


class APIClient:
    """API Client

    `root_url`  : str       ; URL of which all endpoints are in.
    `auth`      : str       ; 'Authorization: ' string

    Usage:
        await get(endpoint) ; returns JSON
        await post(endpoint, data: dict) ; returns JSON
        await patch(endpoint, data: dict) ; return JSON
        await delete(endpoint) ; returns 201
    """

    def __init__(self):
        self.root_url = constants.Api.url
        auth = constants.Api.auth_type + constants.Api.token
        self.session = aiohttp.ClientSession(headers={"Authorization": auth})

    async def close(self):
        """Closes the aiohttp.ClientSession session"""
        await self.session.close()

    async def request(self, method, endpoint, json=None) -> dict:
        async with self.session.request(method, self.root_url + endpoint, json=json) as resp:
            if resp.status < 400:
                json = await resp.json()
                return json.get("data", json)
            try:
                raise ResponseStatusCodeException(resp.status, await resp.json())
            except aiohttp.client_exceptions.ContentTypeError:
                raise ResponseStatusCodeException(resp.status, None)

    async def get(self, endpoint) -> dict:
        """API GET request"""
        return await self.request("GET", endpoint)

    async def post(self, endpoint, data) -> dict:
        """API POST request"""
        return await self.request("POST", endpoint, json=data)

    async def patch(self, endpoint, data) -> dict:
        """API PATCH request"""
        return await self.request("PATCH", endpoint, json=data)

    async def delete(self, endpoint) -> dict:
        """API DELETE request"""
        return await self.request("DELETE", endpoint)
