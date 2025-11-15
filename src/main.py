from __future__ import annotations

import asyncio
from relay import setup as relay_setup
import logging
import math
import tomllib

from aiohttp import web

LOGFMT = "[%(filename)s][%(asctime)s][%(levelname)s] %(message)s"
LOGDATEFMT = "%Y/%m/%d-%H:%M:%S"

handlers = [logging.StreamHandler()]

with open("config.toml") as f:
  config = tomllib.loads(f.read())

if config["log"]["file"]:
  handlers.append(logging.FileHandler(config["log"]))

logging.basicConfig(
  handlers=handlers,
  format=LOGFMT,
  datefmt=LOGDATEFMT,
  level=logging.INFO,
)

LOG = logging.getLogger(__name__)

app = web.Application()

async def startup():
  try:
    app.LOG = LOG
    app.config = config

    await relay_setup(app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
      runner,
      config["srv"]["host"],
      config["srv"]["port"],
    )
    await site.start()
    print(
      f"Started server on http://{config['srv']['host']}:{config['srv']['port']}...\nPress ^C to close..."
    )
    while True:
      await asyncio.sleep(math.inf)

  except KeyboardInterrupt:
    pass

  finally:
    try:
      await site.stop()
    except Exception:
      pass


asyncio.run(startup())
