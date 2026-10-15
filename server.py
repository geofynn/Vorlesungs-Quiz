#!/usr/bin/env python3
"""Kleiner lokaler Quiz-Server – nur Python-Standardbibliothek erforderlich."""

from __future__ import annotations

import argparse
import json
import mimetypes
import socket
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
PLAYER_TIMEOUT_SECONDS = 30
MAX_BODY_BYTES = 8_192
GOAT_COATS = {"snow", "caramel", "chocolate", "cloud", "night"}
GOAT_ACCESSORIES = {"none", "flower", "bow", "cap", "glasses", "crown"}
players: dict[str, dict] = {}
players_lock = threading.Lock()


def clean_players(now: float) -> None:
    expired = [player_id for player_id, player in players.items()
               if now - player["lastSeen"] > PLAYER_TIMEOUT_SECONDS]
    for player_id in expired:
        players.pop(player_id, None)


def public_players(now: float) -> list[dict]:
    clean_players(now)
    return [
        {
            "id": player["id"],
            "name": player["name"],
            "step": player["step"],
            "maxStep": player["maxStep"],
            "fallVersion": player["fallVersion"],
            "goat": player.get("goat", {"coat": "snow", "accessory": "none"}),
        }
        for player in players.values()
    ]


def valid_id(value: object) -> str | None:
    if not isinstance(value, str) or not 1 <= len(value) <= 80:
        return None
    if not all(character.isalnum() or character in "-_" for character in value):
        return None
    return value


def valid_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    name = " ".join(value.split()).strip()[:24]
    return name or None


def bounded_int(value: object, minimum: int, maximum: int) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return max(minimum, min(maximum, value))


def valid_goat(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        value = {}
    coat = value.get("coat")
    accessory = value.get("accessory")
    return {
        "coat": coat if coat in GOAT_COATS else "snow",
        "accessory": accessory if accessory in GOAT_ACCESSORIES else "none",
    }


class QuizHandler(BaseHTTPRequestHandler):
    server_version = "Ziegenquiz/1.1"

    def log_message(self, format_string: str, *args: object) -> None:
        # Die häufigen Statusabfragen würden das Serverfenster sonst überfluten.
        if self.path.startswith("/api/state"):
            return
        print(f"[{self.log_date_time_string()}] {format_string % args}")

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: HTTPStatus) -> None:
        self.send_json({"error": message}, status)

    def read_json(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if length <= 0 or length > MAX_BODY_BYTES:
            return None
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            now = time.monotonic()
            player_id = valid_id(parse_qs(parsed.query).get("playerId", [None])[0])
            with players_lock:
                if player_id in players:
                    players[player_id]["lastSeen"] = now
                state = public_players(now)
            self.send_json({"players": state})
            return

        if parsed.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        file_name = "index.html" if parsed.path in ("/", "/index.html") else None
        if file_name is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        path = ROOT / file_name
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        data = self.read_json()
        if data is None:
            self.send_error_json("Ungültige Anfrage.", HTTPStatus.BAD_REQUEST)
            return

        player_id = valid_id(data.get("id"))
        name = valid_name(data.get("name"))
        goat = valid_goat(data.get("goat"))
        max_step = bounded_int(data.get("maxStep"), 1, 100)
        if player_id is None or name is None or max_step is None:
            self.send_error_json("Spielerangaben sind ungültig.", HTTPStatus.BAD_REQUEST)
            return

        now = time.monotonic()
        with players_lock:
            if parsed.path == "/api/join":
                previous_falls = players.get(player_id, {}).get("fallVersion", 0)
                players[player_id] = {
                    "id": player_id,
                    "name": name,
                    "step": 0,
                    "maxStep": max_step,
                    "fallVersion": previous_falls,
                    "goat": goat,
                    "lastSeen": now,
                }
            elif parsed.path == "/api/progress":
                step = bounded_int(data.get("step"), 0, max_step)
                if step is None:
                    self.send_error_json("Fortschritt ist ungültig.", HTTPStatus.BAD_REQUEST)
                    return
                player = players.setdefault(player_id, {
                    "id": player_id,
                    "name": name,
                    "step": 0,
                    "maxStep": max_step,
                    "fallVersion": 0,
                    "goat": goat,
                    "lastSeen": now,
                })
                player.update(name=name, step=step, maxStep=max_step, goat=goat, lastSeen=now)
                if data.get("wrong") is True:
                    player["step"] = 0
                    player["fallVersion"] += 1
            else:
                self.send_error_json("Nicht gefunden.", HTTPStatus.NOT_FOUND)
                return
            state = public_players(now)
        self.send_json({"players": state})


class QuizServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def local_addresses() -> list[str]:
    addresses: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = info[4][0]
            if not address.startswith("127."):
                addresses.add(address)
    except socket.gaierror:
        pass
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        addresses.add(probe.getsockname()[0])
        probe.close()
    except OSError:
        pass
    return sorted(addresses)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lokaler Server für das Mehrspieler-Ziegenquiz")
    parser.add_argument("--host", default="0.0.0.0", help="Bind-Adresse (Standard: alle Netzwerkschnittstellen)")
    parser.add_argument("--port", type=int, default=8000, help="Port (Standard: 8000)")
    args = parser.parse_args()

    try:
        server = QuizServer((args.host, args.port), QuizHandler)
    except OSError as error:
        raise SystemExit(f"Server konnte nicht gestartet werden: {error}") from error

    print("\nMehrspieler-Ziegenquiz ist gestartet.")
    print(f"Auf diesem Mini-PC: http://localhost:{args.port}")
    for address in local_addresses():
        print(f"Für Teilnehmende:  http://{address}:{args.port}")
    print("\nDieses Fenster geöffnet lassen. Beenden mit Strg+C.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nQuiz-Server beendet.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
