import asyncio
import json
import logging
import os
import random
import string
from pathlib import Path

from aiohttp import WSMsgType, web


WIDTH = 30
HEIGHT = 18
TICK_SECONDS = 0.115
DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
OPPOSITE = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}
GAME_FILE = Path(__file__).with_name("ular_2_pemain.html")
LOGGER = logging.getLogger(__name__)


def new_game():
    return {
        "snakes": [
            {
                "body": [{"x": 5, "y": 8}, {"x": 4, "y": 8}, {"x": 3, "y": 8}],
                "direction": "right",
                "next_direction": "right",
                "turned": False,
            },
            {
                "body": [{"x": 24, "y": 9}, {"x": 25, "y": 9}, {"x": 26, "y": 9}],
                "direction": "left",
                "next_direction": "left",
                "turned": False,
            },
        ],
        "scores": [0, 0],
        "food": None,
        "winner": None,
    }


class Room:
    def __init__(self, code):
        self.code = code
        self.sockets = [None, None]
        self.names = [None, None]
        self.status = "waiting"
        self.game = new_game()
        self.place_food()

    def place_food(self):
        occupied = {
            (part["x"], part["y"])
            for snake in self.game["snakes"]
            for part in snake["body"]
        }
        empty = [
            (x, y)
            for y in range(HEIGHT)
            for x in range(WIDTH)
            if (x, y) not in occupied
        ]
        if empty:
            x, y = random.choice(empty)
            self.game["food"] = {"x": x, "y": y}
        else:
            self.game["food"] = None

    def reset(self):
        self.game = new_game()
        self.place_food()
        self.status = "ready" if all(self.sockets) else "waiting"

    def snapshot(self):
        return {
            "status": self.status,
            "names": self.names,
            "scores": self.game["scores"],
            "snakes": self.game["snakes"],
            "food": self.game["food"],
            "winner": self.game["winner"],
        }


async def send_json(socket, data):
    if socket and not socket.closed:
        try:
            await socket.send_json(data)
        except (ConnectionError, RuntimeError) as error:
            LOGGER.info("WebSocket closed while sending: %s", error)


async def broadcast(room):
    message = {"type": "state", "state": room.snapshot()}
    await asyncio.gather(
        *(send_json(socket, message) for socket in room.sockets if socket),
        return_exceptions=True,
    )


def advance_game(room):
    snakes = room.game["snakes"]
    for snake in snakes:
        snake["direction"] = snake["next_direction"]
        snake["turned"] = False

    heads = []
    eating = []
    for snake in snakes:
        dx, dy = DIRECTIONS[snake["direction"]]
        head = {"x": snake["body"][0]["x"] + dx, "y": snake["body"][0]["y"] + dy}
        heads.append(head)
        food = room.game["food"]
        eating.append(food is not None and head == food)

    def same_cell(first, second):
        return first["x"] == second["x"] and first["y"] == second["y"]

    dead = []
    for index, head in enumerate(heads):
        snake = snakes[index]
        other = snakes[1 - index]
        outside = not (0 <= head["x"] < WIDTH and 0 <= head["y"] < HEIGHT)
        own_body = snake["body"] if eating[index] else snake["body"][:-1]
        other_body = other["body"] if eating[1 - index] else other["body"][:-1]
        dead.append(
            outside
            or any(same_cell(head, part) for part in own_body)
            or any(same_cell(head, part) for part in other_body)
        )

    if same_cell(heads[0], heads[1]) or (
        same_cell(heads[0], snakes[1]["body"][0])
        and same_cell(heads[1], snakes[0]["body"][0])
    ):
        dead = [True, True]

    if any(dead):
        room.status = "finished"
        room.game["winner"] = None if all(dead) else (1 if dead[0] else 0)
        return

    for index, snake in enumerate(snakes):
        snake["body"].insert(0, heads[index])
        if eating[index]:
            room.game["scores"][index] += 1
        else:
            snake["body"].pop()

    if any(eating):
        room.place_food()
        if room.game["food"] is None:
            room.status = "finished"
            room.game["winner"] = "draw"


async def game_loop(app):
    while True:
        await asyncio.sleep(TICK_SECONDS)
        for room in list(app["rooms"].values()):
            if room.status == "running":
                advance_game(room)
                await broadcast(room)


async def start_game_loop(app):
    app["game_task"] = asyncio.create_task(game_loop(app))


async def stop_game_loop(app):
    app["game_task"].cancel()
    try:
        await app["game_task"]
    except asyncio.CancelledError:
        pass


async def index(request):
    return web.FileResponse(
        GAME_FILE,
        headers={"Cache-Control": "no-store, max-age=0"},
    )

async def health(request):
    return web.json_response(
        {"service": "snake-two-player", "websocket": "/ws"},
        headers={"Cache-Control": "no-store"},
    )

def create_room(rooms):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(alphabet, k=6))
        if code not in rooms:
            return Room(code)


async def websocket_handler(request):
    socket = web.WebSocketResponse(heartbeat=25)
    await socket.prepare(request)
    room = None
    player_index = None

    async for message in socket:
        if message.type == WSMsgType.TEXT:
            try:
                data = json.loads(message.data)
            except json.JSONDecodeError:
                await send_json(socket, {"type": "error", "message": "Pesan tidak valid."})
                continue
            if not isinstance(data, dict):
                await send_json(socket, {"type": "error", "message": "Pesan tidak valid."})
                continue

            action = data.get("type")
            if room is None and action in ("create", "join"):
                name = data.get("name", "")
                if not isinstance(name, str):
                    name = ""
                name = name.strip()[:20] or f"Pemain {'1' if action == 'create' else '2'}"

                if action == "create":
                    room = create_room(request.app["rooms"])
                    request.app["rooms"][room.code] = room
                    player_index = 0
                else:
                    code = data.get("code", "")
                    code = code.upper() if isinstance(code, str) else ""
                    room = request.app["rooms"].get(code)
                    if not room:
                        await send_json(socket, {"type": "error", "message": "Kode ruang tidak ditemukan."})
                        room = None
                        continue
                    if room.sockets[1] is not None or room.status != "waiting":
                        await send_json(socket, {"type": "error", "message": "Ruang ini sudah penuh atau permainan sudah dimulai."})
                        room = None
                        continue
                    player_index = 1

                room.sockets[player_index] = socket
                room.names[player_index] = name
                if all(room.sockets):
                    room.status = "ready"
                await send_json(socket, {
                    "type": "joined",
                    "code": room.code,
                    "player": player_index,
                })
                await broadcast(room)
                continue

            if room is None:
                await send_json(socket, {"type": "error", "message": "Buat atau gabung ke ruang terlebih dahulu."})
                continue

            if action == "direction":
                direction = data.get("direction")
                if room.status == "running" and direction in DIRECTIONS:
                    snake = room.game["snakes"][player_index]
                    current = snake["direction"]
                    if not snake["turned"] and direction != OPPOSITE[current]:
                        snake["next_direction"] = direction
                        snake["turned"] = True
            elif action == "start" and room.status in ("ready", "paused"):
                room.status = "running"
                await broadcast(room)
            elif action == "pause" and room.status == "running":
                room.status = "paused"
                await broadcast(room)
            elif action == "reset":
                room.reset()
                await broadcast(room)

        elif message.type in (WSMsgType.ERROR, WSMsgType.CLOSE, WSMsgType.CLOSED):
            break

    if room is not None:
        request.app["rooms"].pop(room.code, None)
        for other_index, other_socket in enumerate(room.sockets):
            if other_index != player_index and other_socket:
                await send_json(other_socket, {"type": "room_closed"})
    return socket


def create_app():
    app = web.Application()
    app["rooms"] = {}
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/ws", websocket_handler)
    app.on_startup.append(start_game_loop)
    app.on_cleanup.append(stop_game_loop)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
