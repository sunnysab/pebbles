
from typing import List
import asyncio
import aiohttp
import aiofiles


class AsyncDownloader:

    _session: aiohttp.ClientSession = None

    async def __download_file(self, url: str, output_path: str):
        output_file = await aiofiles.open(output_path, 'wb')
        response = await self._session.get(url)
        
        async for chunk in response.content.iter_chunked(1024 * 1024):
            await output_file.write(chunk)


    async def download_files(self, url_list: List[str], output_directory: str) -> List[str]:
        if not output_directory.endswith('/'):
            output_directory += '/'
        if not self._session:
            self._session = aiohttp.ClientSession()

        output_filelist = [output_directory + f'{index}.mp4' for index in range(len(url_list))]
        futures = [
            self.__download_file(url, filename)
            for url, filename in zip(url_list, output_filelist)
        ]
        await asyncio.gather(*futures)

        self._session.close()
        return output_filelist