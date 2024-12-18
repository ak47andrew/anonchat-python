from __future__ import annotations
import websockets
import asyncio
import json
from . import auth
from . import utils
from typing import Optional, AsyncIterator, overload


BASE_URL = "wss://anonchatapi.stivisto.com/socket.io/"
# BASE_URL = "ws://localhost:1234"  # For debug :3


class Bot:
    def __init__(self, auth_dict: dict[str, str], autologin: bool = True):
        params = auth.generate_data() | auth_dict
        self.autologin = autologin
        self.uri = utils.generate_uri(BASE_URL, params)
        self.cookie = auth_dict["cookie"]
        self.websocket = None
        self.pending_responses = {}
        self._message_queue = asyncio.Queue()  # Queue for async iterator
        self.api = self.API(self)

    # Feel free to redefine it both via subclasses and attributes
    async def on_ready_hook(self):
        pass

    async def connect(self):
        """Connect to the WebSocket server."""
        self.websocket = await websockets.connect(self.uri)
        asyncio.create_task(self._listen_for_responses())

    async def _listen_for_responses(self):
        """Listen for incoming messages and resolve pending responses."""
        if self.websocket is None:
            raise RuntimeError("WebSocket is not connected")
        try:
            async for message in self.websocket:
                print(f"Raw message: {message}")
                # Ping-pong handling
                message = str(message)  # More of a type checking thing. kinda ugly, but okay
                if message == "2":
                    await self.websocket.send("3")
                else:
                    # Add messages to the queue for the iterator
                    await self._message_queue.put(message)
                    # Handle the message internally
                    await self._handle_response(message)
        except websockets.ConnectionClosed:
            print("Connection closed")

    async def _handle_response(self, message: str):
        """Handle incoming messages, resolving any pending responses."""
        try:
            print("Received message:", message)
            if self.autologin and message.startswith("0{"):
                await self.send_message("40")
                return
            if message.startswith("40{"):
                await self.on_ready_hook()
                if self.autologin:
                    return
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
    
    @overload
    async def send_message_with_response(self, /, message_or_id: str):
        pass

    @overload
    async def send_message_with_response(self, /, message_or_id: int, method: Optional[str], params: Optional[dict | list]):
        pass

    async def send_message_with_response(self, /, message_or_id: int | str, method: Optional[str] = None, params: Optional[dict | list] = None):
        """Send a message and wait for a response."""
        if not self.websocket:
            raise RuntimeError("WebSocket is not connected")

        if isinstance(message_or_id, str):
            id_ = utils.get_data_ws_msg(message_or_id)[0]
            message = message_or_id
        else:
            id_ = message_or_id
            message = utils.format_ws_msg(id_, method, params)
        recv_id = utils.generate_recv_id(id_)

        print(f"Send: {message}")

        future = asyncio.Future()
        self.pending_responses[recv_id] = future

        await self.websocket.send(message)
        return await future

    async def __aenter__(self):
        """Enter the asynchronous context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the asynchronous context manager."""
        await self.disconnect()

    async def disconnect(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def __aiter__(self) -> AsyncIterator[str]:
        """Make the Bot class an async iterator to yield incoming WebSocket messages."""
        while self.websocket:  # Keep yielding messages while connected
            try:
                message = await self._message_queue.get()  # Wait for messages in the queue
                yield message  # Yield the message to the iterator's consumer
            except asyncio.CancelledError:
                break  # Stop iteration if the task is cancelled
            except Exception as e:
                print(f"Error in async iterator: {e}")
                break
    
    class API:
        def __init__(self, outer_instance: Bot) -> None:
            self.outer_instance = outer_instance
