#!/usr/bin/env python3
from os import path as ospath, walk
from aiofiles.os import path as aiopath, rename as aiorename
from asyncio import sleep
from aiohttp import ClientSession

from bot import LOGGER
from bot.helper.ext_utils.bot_utils import sync_to_async

ALLOWED_EXTS = [
	'.avi', '.mkv', '.mpg', '.mpeg', '.vob', '.wmv', '.flv', '.mp4', '.mov', '.m4v',
	'.m2v', '.divx', '.3gp', '.webm', '.ogv', '.ogg', '.ts', '.ogm'
]

API_KEY = "398163bd8074vqvx2lyn6o"


class Doodstream:
	"""docstring for Doostream"""

	def __init__(self, dluploader):
		self.apiKey = API_KEY
		self.dluploader = dluploader
		self.base_url = "https://doodapi.com"

	async def __resp_handler(self, response):
		api_resp = response.get("status", "")
		if api_resp == "ok":
			return response["data"]
		raise Exception(api_resp.split("-")[1] if "error-" in api_resp else "Response Status is not ok and Reason is Unknown")


	async def __getAccInfo(self):
		async with ClientSession() as session, session.get(f"{self.base_url}/api/account/info?key={self.apiKey}") as response:
			if response.status == 200:
				if (data := await response.json()) and data["status"] == 200:
					return data["result"]
		return None

	async def __getServer(self):
		async with ClientSession() as session:
			async with session.get(f"{self.base_url}/api/upload/server?key={self.apiKey}") as resp:
				LOGGER.debug(resp.json())
				return await resp.json()

	async def upload_file(self, path: str):
		server = (await self.__getServer())["result"]
		apiKey = self.apiKey if self.apiKey else ""
		req_dict = {}
		if apiKey:
			req_dict["api_key"] = apiKey


		if self.dluploader.is_cancelled:
			return
		new_path = ospath.join(ospath.dirname(path), ospath.basename(path).replace(' ', '.'))
		await aiorename(path, new_path)
		self.dluploader.last_uploaded = 0
		upload_file = await self.dluploader.upload_aiohttp(f"{server}", new_path, "file", req_dict)
		LOGGER.debug(upload_file)
		return await upload_file

	async def upload(self, file_path):
		if not await self.__getAccInfo():
			raise Exception("Invalid doodstream API Key, Recheck your account !!")
		if await aiopath.isfile(file_path):
			if (gCode := await self.upload_file(path=file_path)) and gCode.get("download_url", False):
				return gCode['download_url']
		if self.dluploader.is_cancelled:
			return
		raise Exception("Failed to upload file/folder to doodstream API, Retry or Try after sometimes...")