import websockets
import asyncio
import json
from . import auth
from . import utils
from typing import Optional


BASE_URL = "wss://anonchatapi.stivisto.com/socket.io/"


class Bot:
    def __init__(self, auth_dict: dict[str, str]):
        params = auth.generate_data() | auth_dict
        self.uri = utils.generate_uri(BASE_URL, params)
        self.cookie = auth_dict["cookie"]
        self.websocket = None
        self.pending_responses = {}

    async def connect(self):
        """Connect to the WebSocket server."""
        self.websocket = await websockets.connect(self.uri)
        asyncio.create_task(self._listen_for_responses())

    async def _listen_for_responses(self):
        """Listen for incoming messages and resolve pending responses."""
        try:
            async for message in self.websocket:
                # Ping-pong handling
                if message == "2":
                    await self.websocket.send("3")
                else:
                    self._handle_response(message)
        except websockets.ConnectionClosed:
            print("Connection closed")

    def _handle_response(self, message):
        """Handle incoming messages, resolving any pending responses."""
        try:
            print("Received message:", message)
            id_, name, params = utils.get_data_ws_msg(message)
            if id_ in self.pending_responses:
                future: asyncio.Future = self.pending_responses.pop(id_)
                if not future.done():
                    future.set_result(params)
        except json.JSONDecodeError:
            print("Received invalid message:", message)

    async def send_message(self, message: str):
        """Send a message without waiting for a response."""
        if self.websocket:
            print(f"Fire and forget: {message}")
            await self.websocket.send(message)
        else:
            raise RuntimeError("WebSocket is not connected")

    async def send_message_with_response(self, id_: int, method: Optional[str] = None, params: Optional[dict | list] = None):
        """Send a message and wait for a response."""
        if not self.websocket:
            raise RuntimeError("WebSocket is not connected")

        recv_id = utils.generate_recv_id(id_)
        message = utils.format_ws_msg(id_, method, params)
        print(f"Send: {message}")

        future = asyncio.Future()
        self.pending_responses[recv_id] = future

        await self.websocket.send(message)
        return await future

    async def disconnect(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    # async def run(self):
    #     """Run the bot, connecting to the WebSocket server, creating an infinite loop, and disconnecting when it's closed."""
    #     try:
    #         await self.connect()
    #         print("Bot connected")
    #         future = asyncio.Future()
    #         while not future.done():
    #             pass
    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #
    #     finally:
    #         await self.disconnect()
    #         print("Bot disconnected")
