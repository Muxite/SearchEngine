import pytest
from DataGatherer.app.Crawler import Crawler
import asyncio
from queue import Queue

import time

@pytest.mark.asyncio
async def test_crawler():
    target_links = Queue()
    link_text = Queue()
    potential_links = Queue()

    crawler = Crawler(target_links, link_text, potential_links, 5)

    await crawler.start(8)
    assert len(crawler.worker_tasks) == 8

    await asyncio.to_thread(target_links.put, "https://muxite.github.io/test")

    link, text = await asyncio.to_thread(link_text.get)
    pot_link = await asyncio.to_thread(potential_links.get)

    assert link == "https://muxite.github.io/test"

    assert text == ("Test | Test Test Mayonaka no Door Hype Boy Neon Genesis Evangelion"
                    " test test test test test Google Wikipedia")

    assert pot_link == "https://www.google.com/"

    await crawler.stop()

test_crawler()