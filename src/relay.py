from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
from aiohttp import web
from utils.hash import channel_hash

if TYPE_CHECKING:
  from typing import Iterable

# This file will handle all of the /ws and /node logic.

routes = web.RouteTableDef()

class Channel:
  name: str
  passwd: str
  clients: list[Client]

  def __init__(self, name: str, passwd: str):
    self.name = name
    self.passwd = passwd
    self.clients = []

  async def send_message(self, message: str, skip: Iterable[Client]) -> None:
    for client in self.clients:
      if client not in skip:
        await client.send_message(message, self.name)

    # TODO: implement multi-node logic

channels: dict[str, Channel] = {} # Hashmap name: channel

class Client:
  channels: list[Channel]
  ws: web.WebSocketResponse

  def __init__(self):
    self.channels = []

  async def send_message(self, message: str, channel: str) -> None:
    payload = {
      "type": "message",
      "data": {
        "message": message,
        "channel": channel
      }
    }
    
    await self.ws.send_json(payload)

  async def subscribe_channel(self, chan_name: str, passwd: str = None) -> str:
    if chan_name in channels:
      # Channel exists, lets check authorization.
      channel: Channel = channels[chan_name]
      if channel.passwd:
        if not passwd:
          return "invalid password"
        hashword = channel_hash(channel.name, passwd)
        if hashword != channel.passwd:
          return "invalid password"
        channel.clients.append(self)
        self.channels.append(channel)
      else: # No password, just subscribe.
        channel.clients.append(self)
        self.channels.append(channel)
        return "ok"
    else:
      if passwd:
        channel_passwd = channel_hash(chan_name, passwd)
      else:
        channel_passwd = None
      channel = Channel(chan_name, channel_passwd)
      channels[chan_name] = channel
      
      # TODO: Implement reserving logic for multi-node

      channel.clients.append(self)
      self.channels.append(channel)
      return "ok"


  async def unsubscribe_channel(self, chan_name: str) -> None:
    if chan_name not in channels:
      return "channel does not exist"
    
    channel = channels[chan_name]
    self.channels.remove(channel)
    channel.clients.remove(self)

    if len(channel.clients) == 0:
      del channels[chan_name]

      # TODO: multi-node unreserving logic
    
    return "ok"

  async def handle_websocket(self, request: web.Request) -> None:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    self.ws = ws

    async for msg in ws:
      if msg.type == aiohttp.WSMsgType.TEXT:
        try:
          received_packet = msg.json()

          nonce = received_packet.get("nonce", "")

          if "command" not in received_packet:
            await ws.send_json({
              "type": "error",
              "data": {
                "reason": "command key must be present"
              },
              "nonce": nonce
            })
            continue

          command = received_packet.get("command")
          data = received_packet.get("data", None)

          if command not in ["subscribe", "unsubscribe", "list", "send"]:
            await ws.send_json({
              "type": "error",
              "data": {
                "reason": "invalid command"
              },
              "nonce": nonce
            })
            continue

          if data is None:
            await ws.send_json({
              "type": "error",
              "data": {
                "reason": "data key must be present"
              },
              "nonce": nonce
            })
            continue

          
          if command == "subscribe":
            # Check the contents of the data packet.
            channel_name = data.get("channel", None)
            if channel_name is None:
              await ws.send_json({
                "type": "error",
                "data": {
                  "reason": "no channel provided"
                },
                "nonce": nonce
              })
            
            password = data.get("password", None)
            result = await self.subscribe_channel(channel_name, password)
            if result == "ok":
              await ws.send_json({
                "type": "response",
                "data": {
                  "ok": True
                },
                "nonce": nonce
              })
            else:
              await ws.send_json({
                "type": "response",
                "data": {
                  "ok": False,
                  "reason": result
                },
                "nonce": nonce
              })

          elif command == "unsubscribe":
            # Check the contents of the data packet.
            channel_name = data.get("channel", None)
            if channel_name is None:
              await ws.send_json({
                "type": "error",
                "data": {
                  "reason": "no channel provided"
                },
                "nonce": nonce
              })
            
            result = await self.unsubscribe_channel(channel_name, password)
            if result == "ok":
              await ws.send_json({
                "type": "response",
                "data": {
                  "ok": True
                },
                "nonce": nonce
              })
            else:
              await ws.send_json({
                "type": "response",
                "data": {
                  "ok": False,
                  "reason": result
                },
                "nonce": nonce
              })

          elif command == "list":
            # There shouldn't be any data for this command, so don't bother checking.
            channel_list = [channel.name for channel in self.channels]
            await ws.send_json({
              "type": "response",
              "data": {
                "ok": True,
                "channels": channel_list
              },
              "nonce": nonce
            })

          elif command == "send":
            if "message" not in data:
              await ws.send_json({
                "type": "response",
                "data": {
                  "ok": False,
                  "reason": "message key must be present"
                },
                "nonce": nonce
              })
              continue
            if "channel" not in data:
              await ws.send_json({
                "type": "response",
                "data": {
                  "ok": False,
                  "reason": "message key must be present"
                },
                "nonce": nonce
              })
              continue

            if data["channel"] in channels:
              channel = channels[data["channel"]]
            else:
              await ws.send_jsion({
                "type": "response",
                "data": {
                  "ok": False,
                  "reason": "channel does not exist"
                },
                "nonce": nonce
              })
              continue
            
            if channel not in self.channels:
              await ws.send_jsion({
                "type": "response",
                "data": {
                  "ok": False,
                  "reason": "channel does not exist"
                },
                "nonce": nonce
              })
              continue
            
            await channel.send_message(data["message"], [self])


        except Exception:
          pass

routes = web.RouteTableDef()

@routes.get("/connect")
async def get_connect(request: web.Request) -> web.Response:
  c = Client()
  return await c.handle_websocket(request)

async def setup(app: web.Application) -> None:
  app.add_routes(routes)