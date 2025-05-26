import asyncio
from queue import Empty
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse

try:
    from utils import push_list
except ImportError:
    from DataGatherer.app.utils import push_list



class Crawler:
    def __init__(self, target_links, link_text, potential_links, timeout):
        """
        Uses aiohttp to use target links to get link text and potential links.
        :param target_links: Queue of target links to visit.
        :param link_text: Queue of link, text pairs.
        :param potential_links: Queue of potential links to visit later.
        :param timeout: Timeout in seconds.
        """
        self.target_links = target_links
        self.link_text = link_text
        self.potential_links = potential_links
        self.timeout = timeout
        self.running = False
        self.worker_tasks = []

    async def start(self, workers):
        """
        Start the crawler with a number of workers.
        :param workers: Number of workers.
        """
        if self.running:
            return
        self.running = True
        for _ in range(workers):
            self.worker_tasks.append(asyncio.create_task(self.worker()))

    async def stop(self, soft=False):
        """
        Stop the crawler, can hard stop or soft.
        :param soft: Crawler waits for target links to be used up.
        """
        self.running = False
        if soft:
            await self.target_links.join()
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()

    async def worker(self):
        """
        Primary event loop for crawling.
        """
        async with ClientSession(timeout=ClientTimeout(total=self.timeout)) as session:
            while self.running:
                try:
                    # try to get a link
                    link = await asyncio.to_thread(self.target_links.get_nowait)
                except Empty:
                    await asyncio.sleep(self.timeout)
                    continue

                try:
                    await self.get_link(session, link)

                finally:
                    self.target_links.task_done()

    async def get_link(self, session, link):
        async with session.get(link) as response:
            if response.status != 200:
                return
            html = await response.text()

        # combine this with each tag content to form the full link.
        # we do not have a browser this time.
        base_url = f"{urlparse(link).scheme}://{urlparse(link).netloc}"

        soup = BeautifulSoup(html, "html.parser")
        body = soup.get_text(separator=" ", strip=True)

        await asyncio.to_thread(self.link_text.put, (link, body))

        for found_link in soup.find_all("a", href=True):
            full_link = urljoin(base_url, found_link["href"])
            await asyncio.to_thread(self.potential_links.put, full_link)
