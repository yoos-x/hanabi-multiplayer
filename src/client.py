import socket
import threading
import pickle
import logging

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.game_state import GameLogic


class HanabiClient:
    def __init__(self):
        # logging initialize
        logging.basicConfig(
            level=logging.INFO,
            filename="client.log",
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("HanabiClient")
        self.is_german = True

        self.client_socket = None
        self.connected = False

        # game state
        self.username = ""
        self.server_ip = ""
        self.games = []
        self.online_users = []
        self.chat_history = []
        self.callbacks = {}
        self.current_room = None

    def set_callback(self, event, callback):
        self.callbacks[event] = callback

    def _trigger_callback(self, event, *args, **kwargs):
        if event in self.callbacks:
            self.callbacks[event](*args, **kwargs)

    def auto_refresh_lobby(self, interval=2.0):
        if self.connected:
            threading.Timer(interval, self.auto_refresh_lobby, [interval]).start()

    def connect_to_server(self, server_ip, port):
        if not self.username.strip():
            self.logger.error("Username is required to connect to the server.")
            return False

        if server_ip == "0.0.0.0":
            self.logger.error(
                "Cannot connect to '0.0.0.0'. Please provide a valid server IP."
            )
            return False

        try:
            port = int(port)
            if port < 1024 or port > 65535:
                self.logger.error("Invalid port! Port must be between 1024 and 65535.")
                return False

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)  # Add timeout of 5 seconds
            self.client_socket.connect((server_ip, port))
            self.client_socket.settimeout(None)  # Reset timeout to default

            self.client_socket.sendall(
                pickle.dumps({"type": "join", "name": self.username})
            )
            self.connected = True
            threading.Thread(target=self.receive_data, daemon=True).start()
            if self.connected:
                self.auto_refresh_lobby(interval=5.0)
            self._trigger_callback("connected")
            return True

        except socket.timeout:
            self.logger.error("Connection timed out. Please check the IP and port.")
            return False
        except ConnectionRefusedError:
            self.logger.error(
                "Connection refused. Please check if the server is running."
            )
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
            return False

    def receive_data(self):
        self.logger.info("Starting to receive data from server.")
        while self.connected:
            try:
                raw_data = self.client_socket.recv(4096)

                try:
                    data = pickle.loads(raw_data)
                    self.logger.info(f"Decoded data: {data}")
                except Exception as e:
                    self.logger.error(f"Failed to decode data: {e}")
                    continue

                self.handle_server_message(data)
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                self.connected = False

    def handle_server_message(self, message):
        msg_type = message.get("type", "")

        if msg_type == "lobby_update":
            self.games = message.get("games", [])
            self.online_users = message.get("users", [])
            self.chat_history = message.get("chat_history", [])
            self._trigger_callback("lobby_update")

        elif msg_type == "room_update":
            self.logger.info(f"Received room_update: {message}")
            room_name = message.get("room_name")
            if not room_name:
                self.logger.error("room_update message missing 'room_name'")
                return
            elif self.current_room and self.current_room["room_name"] == room_name:
                self.logger.info(
                    f"Triggering room_update callback for room: {room_name}"
                )
                self.current_room.update(message)
                self._trigger_callback("room_update", message)
            else:
                self.logger.warning(
                    f"room_update received for unmatched room: {room_name}"
                )

        elif msg_type == "chat":
            self.chat_history.append(message.get("message"))
            self.logger.info(f"Chat message received: {message['message']}")
            self._trigger_callback("chat_update")

        elif msg_type == "game_start":
            # Only start game if we're not already in a game
            if not hasattr(self, "in_game") or not self.in_game:
                self.logger.info("Received game start message")
                self.in_game = True
                self.game_logic = GameLogic(
                    players=message["players"],
                    username=self.username,
                    host=message["host"],
                    variant=message["variant"],
                    total_storm_cards=message["total_storm_cards"],
                    max_clue_number=message["max_clue_number"],
                )
                if "initial_state" in message:
                    self.game_logic.set_state(message["initial_state"])

                self._trigger_callback("game_start", self.game_logic)
                self.logger.info("Game start callback triggered")

        elif msg_type == "game_update":
            self.logger.info(f"Received game state update: {message}")
            if "game_state" not in message or not message["game_state"]:
                self.logger.error("Received game_update without game_state!")
                return

            game_state = message["game_state"]

            if self.in_game and hasattr(self, "game_logic"):
                self.logger.info(f"Applying game state: {game_state}")
                self.game_logic.update_state(game_state)
                self._trigger_callback("game_update")
                self.logger.info("Game update applied, UI refreshed.")

        elif msg_type == "error":
            self.logger.error(f"Server error: {message.get('message')}")

        else:
            self.logger.warning(f"Unknown message type received: {msg_type}")

    def send_message(self, message_type, **data):
        if self.connected:
            data["type"] = message_type
            try:
                serialized_data = pickle.dumps(data)
                self.client_socket.sendall(serialized_data)
                if message_type != "get_lobby_update":
                    self.logger.info(f"Message sent: {data}")
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
                self.connected = False

    ########## about Game ##########
    def create_game(
        self, room_name, max_players, variant, total_storm_cards, max_clue_number
    ):
        self.send_message(
            "create_room",
            room_name=room_name,
            max_players=max_players,
            variant=variant,
            total_storm_cards=total_storm_cards,
            max_clue_number=max_clue_number,
        )
        self.current_room = {
            "room_name": room_name,
            "players": [self.username],
            "max_players": max_players,
            "variant": variant,
            "total_storm_cards": total_storm_cards,
            "max_clue_number": max_clue_number,
            "status": "waiting",
            "host": self.username,
        }
        self.logger.info(f"Created game: {self.current_room}")

    def join_game(self, room_name):
        self.send_message("join_room", room_name=room_name)
        for game in self.games:
            if game["room_name"] == room_name:
                self.current_room = game
                break

    def leave_game(self, room_name):
        try:
            self.send_message("leave_room", room_name=room_name)
            self.current_room = None
            self.logger.info(f"Left the room: {room_name}")
            self.send_message("get_lobby_update")

        except Exception as e:
            self.logger.error(f"Failed to leave the room: {e}")

    def exit_game(self):
        if self.current_room:
            self.send_message("leave_room", room_name=self.current_room["room_name"])
            self.current_room = None
            # Reset game-related states
            self.in_game = False
            if hasattr(self, "game_logic"):
                delattr(self, "game_logic")
        self.send_message("get_lobby_update")

    def start_game(self, room_name):
        self.send_message("start_game", room_name=room_name)

    def send_chat_message(self, message):
        self.send_message("chat", name=self.username, message=message)

    def disconnect(self):
        if self.connected:
            try:
                self.send_message("signout", name=self.username)
                self.logger.info(f"User {self.username} signed out.")
            except Exception as e:
                self.logger.error(f"Failed to sign out: {e}")

        self.connected = False
        if self.client_socket:
            self.client_socket.close()

        self._trigger_callback("lobby_update")  # lobby render force

    def send_player_actions(self):
        player_action = self.get_game_state()
        if self.connected:
            try:
                self.client_socket.sendall(pickle.dumps(player_action))
                response = self.client_socket.recv(4096)
                return pickle.loads(response)
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
                self.connected = False
