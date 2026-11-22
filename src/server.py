import socket
import threading
import pickle
import logging
from datetime import datetime
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.game_state import GameLogic


class HanabiServer:
    def __init__(self, host=None, port=None):
        # Initialize Logger
        logging.basicConfig(
            level=logging.INFO,
            filename="server.log",
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("HanabiServer")

        # read config.json
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as file:
                config = json.load(file)
            default_host = config["server"]["host"]
            default_port = config["server"]["port"]
        else:
            self.logger.warning(
                "Warning: config.json not found! Using default settings."
            )
            default_host = "0.0.0.0"
            default_port = 12345

        # If no port is provided, use the default value.
        if port is None:
            port = default_port
        while True:
            try:
                port = int(port)
                if 1024 <= port <= 65535:
                    break
                else:
                    print("Invalid port! Port must be between 1024 and 65535.")
            except ValueError:
                print("Invalid input! Please enter a valid port number.")

            port = input(" Please enter a valid port (1024-65535): ")

        # If the IP and port are entered manually, override the default values.
        self.host = host if host else default_host
        self.port = port if port else default_port

        # Write the latest IP/Port to "config.json"
        self.update_config()

        # bind host and port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.clients = []  # Connected clients
        self.players = []  # Player information
        self.chat_history = []  # Chat history
        self.rooms = []  # Game rooms

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            filename="server.log",
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("HanabiServer")
        self.logger.info(f"Server initialized on {host}:{port}")

    def update_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config = {"server": {"host": self.host, "port": self.port}}

        with open(config_path, "w") as file:
            json.dump(config, file, indent=2)

        if hasattr(
            self, "logger"
        ):  # Avoid errors when the logger is not yet initialized.
            self.logger.info(
                f"Updated config.json with host={self.host}, port={self.port}"
            )

    ########## basics ##########
    def start(self):
        # Start the server
        self.logger.info("Server started, waiting for connections...")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                self.logger.info(f"New connection from {addr}")
                threading.Thread(
                    target=self.handle_client, args=(client_socket, addr), daemon=True
                ).start()
        except KeyboardInterrupt:
            self.logger.info("Server shutting down...")
        finally:
            for client in self.clients:
                try:
                    client["socket"].close()
                except:  # noqa: E722
                    pass
            self.server_socket.close()
            self.logger.info("Server stopped")

    def broadcast(self, data=None):
        # Broadcast data to all clients
        if data is None:
            data = {
                "type": "lobby_update",
                "games": [
                    {
                        "room_name": room["room_name"],
                        "players": room["players"],
                        "max_players": room["max_players"],
                        "variant": room["variant"],
                        "status": room["status"],
                        "total_storm_cards": room["total_storm_cards"],
                        "max_clue_number": room["max_clue_number"],
                        "host": room["host"],
                    }
                    for room in self.rooms
                ],
                "users": [
                    {"name": player["name"], "status": player["status"]}
                    for player in self.players
                ],
                "chat_history": self.chat_history[-50:],
            }

        for client in self.clients[:]:  # Create a copy using slicing
            try:
                client["socket"].sendall(pickle.dumps(data))
            except Exception as e:
                self.logger.error(f"Broadcasting error: {e}")
                self.disconnect_client(client["socket"])

    def handle_client(self, client_socket, addr):
        # Handle client connection
        client_info = {"socket": client_socket, "name": None, "addr": addr}

        try:
            while True:
                raw_data = client_socket.recv(4096)

                if not raw_data:
                    self.logger.warning(
                        f"Empty data received from {addr}. Disconnecting client."
                    )
                    break

                if not isinstance(raw_data, bytes):
                    self.logger.error("Data is not in bytes format!")
                    continue

                try:
                    data = pickle.loads(raw_data)
                    self.logger.info(f"Decoded data: {data}")
                except Exception as e:
                    self.logger.error(f"Failed to decode data: {e}")
                    continue

                msg_type = data.get("type", "")
                if msg_type == "join":
                    self.handle_join(client_info, data)
                elif msg_type == "chat":
                    self.handle_chat(client_info, data)
                elif msg_type == "create_room":
                    self.handle_create_room(client_info, data)
                elif msg_type == "join_room":
                    self.handle_join_room(client_info, data)
                elif msg_type == "leave_room":
                    self.handle_leave_room(client_info, data)
                elif msg_type == "start_game":
                    self.handle_start_game(client_info, data)
                elif msg_type == "game_action":
                    self.handle_game_action(client_info, data)
                elif msg_type == "game_update":
                    self.handle_game_update(client_info, data)
                elif msg_type == "signout":
                    self.logger.info(f"User {data['name']} is signing out.")
                    self.disconnect_client(client_socket)
                    self.broadcast()  # broadcast signout
                elif msg_type == "get_lobby_update":
                    pass
                else:
                    self.logger.warning(f"Unknown message type: {msg_type}")

        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
        finally:
            self.disconnect_client(client_socket)

    def send_error(self, client_socket, error_message):
        # Send error message to a client
        try:
            client_socket.sendall(
                pickle.dumps({"type": "error", "message": error_message})
            )
        except Exception as e:
            self.logger.error(f"Error sending error message: {e}")

    def disconnect_client(self, client_socket):
        # Handle client disconnection
        client_info = next(
            (c for c in self.clients if c["socket"] == client_socket), None
        )

        if client_info:
            self.clients.remove(client_info)
            if client_info["name"]:
                # Remove from player list
                self.players = [
                    p for p in self.players if p["name"] != client_info["name"]
                ]

                # Remove from all rooms
                for room in self.rooms[:]:  # Create a copy using slicing
                    if client_info["name"] in room["players"]:
                        room["players"].remove(client_info["name"])
                        if not room["players"]:
                            self.rooms.remove(room)
                        elif client_info["name"] == room["host"] and room["players"]:
                            room["host"] = room["players"][0]

            try:
                client_socket.close()
            except:  # noqa: E722
                pass

            self.logger.info(f"Client disconnected: {client_info['name'] or 'Unknown'}")
            self.broadcast()

    ########## in LoginPage ##########
    def handle_join(self, client_info, data):
        # Handle player joining the server
        username = data["name"]

        # Check if the username already exists
        if any(player["name"] == username for player in self.players):
            self.send_error(client_info["socket"], "Username already taken")
            return

        client_info["name"] = username
        self.clients.append(client_info)
        self.players.append(
            {"name": username, "status": "In Lobby", "addr": client_info["addr"]}
        )

        self.logger.info(f"Player {username} joined from {client_info['addr']}")
        self.send_lobby_update(client_info["socket"])
        self.broadcast()

    ########## in GameListPage ##########
    def send_lobby_update(self, client_socket):
        # Send current lobby information to a single client"
        data = {
            "type": "lobby_update",
            "games": [
                {
                    "room_name": room["room_name"],
                    "players": room["players"],
                    "max_players": room["max_players"],
                    "variant": room["variant"],
                    "status": room["status"],
                    "host": room["host"],
                }
                for room in self.rooms
            ],
            "users": [
                {"name": player["name"], "status": player["status"]}
                for player in self.players
            ],
            "chat_history": self.chat_history[-50:],
        }
        try:
            client_socket.sendall(pickle.dumps(data))
        except Exception as e:
            self.logger.error(f"Error sending lobby update: {e}")

    def handle_chat(self, client_info, data):
        # Handle chat messages

        if not client_info["name"]:
            return

        message = {
            "name": data["name"],
            "message": data["message"],
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        self.chat_history.append(message)
        self.logger.info(f"Chat message received: {message}")
        self.broadcast({"type": "chat", "message": message})

    ########## in NewGamePage ##########
    def handle_create_room(self, client_info, data):
        if not client_info["name"]:
            return

        room_name = data["room_name"]

        # Check if the room name already exists
        if any(room["room_name"] == room_name for room in self.rooms):
            self.send_error(client_info["socket"], "Room name already exists")
            return

        new_room = {
            "room_name": room_name,
            "players": [client_info["name"]],
            "max_players": data["max_players"],
            "variant": data["variant"],
            "status": "warten",
            "total_storm_cards": data["total_storm_cards"],
            "max_clue_number": data["max_clue_number"],
            "host": client_info["name"],
            "game_state": None,
        }

        self.rooms.append(new_room)
        self.update_player_status(client_info["name"], f"In Raum: {room_name}")
        self.logger.info(f"Room '{room_name}' created by {client_info['name']}")
        self.broadcast()

    ########## in WaitingPage ##########
    def handle_join_room(self, client_info, data):
        # Handle join room request
        if not client_info["name"]:
            return

        room_name = data["room_name"]
        room = next((r for r in self.rooms if r["room_name"] == room_name), None)

        if not room:
            self.send_error(client_info["socket"], "Room not found")
            return
        elif len(room["players"]) >= room["max_players"]:
            self.send_error(client_info["socket"], "Room is full")
            return
        elif room["status"] != "warten":
            self.send_error(client_info["socket"], "Game already started")
            return

        room["players"].append(client_info["name"])

        self.update_player_status(client_info["name"], f"In Raum: {room_name}")
        self.logger.info(f"Player {client_info['name']} joined room '{room_name}'")
        self.broadcast_to_room(
            room,
            {
                "type": "room_update",
                "room_name": room["room_name"],
                "players": room["players"],
                "max_players": room["max_players"],
                "variant": room["variant"],
                "total_storm_cards": room["total_storm_cards"],
                "max_clue_number": room["max_clue_number"],
                "status": room["status"],
                "host": room["host"],
            },
        )
        self.broadcast()  # Update the lobby info

    def handle_leave_room(self, client_info, data):
        if not client_info["name"]:
            return

        room_name = data["room_name"]
        room = next((r for r in self.rooms if r["room_name"] == room_name), None)

        if room and client_info["name"] in room["players"]:
            room["players"].remove(client_info["name"])
            self.update_player_status(client_info["name"], "In Lobby")
            self.logger.info(f"Player {client_info['name']} left room {room_name}.")

            # Reset room status if game was in progress
            if room["status"] == "spielt":
                room["status"] = "warten"

            # If the room is empty, remove it
            if not room["players"]:
                self.rooms.remove(room)
            # If the host leaves, assign a new host
            elif client_info["name"] == room["host"] and room["players"]:
                room["host"] = room["players"][0]
                room["status"] = "warten"  # Reset status when host changes

            self.logger.info(f"Player {client_info['name']} left room '{room_name}'")
            self.broadcast_to_room(
                room,
                {
                    "type": "room_update",
                    "room_name": room["room_name"],
                    "players": room["players"],
                    "max_players": room["max_players"],
                    "variant": room["variant"],
                    "status": room["status"],
                    "host": room["host"],
                },
            )
            self.broadcast()  # Update the lobby info

    ########## in GamingPage ##########
    def handle_start_game(self, client_info, data):
        # Handle start game request
        if not client_info["name"]:
            return

        room_name = data["room_name"]
        room = next((r for r in self.rooms if r["room_name"] == room_name), None)

        if not room:
            return
        # Checking if game is already started
        if room.get("status") == "spielt":
            return

        if room["host"] != client_info["name"]:
            self.send_error(client_info["socket"], "Only host can start the game")
            return

        if len(room["players"]) < 2:
            self.send_error(client_info["socket"], "Need at least 2 players to start")
            return
        # Updating room status
        room["status"] = "spielt"
        self.logger.info(
            "START_GAME event before logic initialization"
        )  # for debugging

        # Initialize game logic and state
        game_logic = GameLogic(
            players=room["players"],
            username=room["host"],
            host=room["host"],
            variant=room["variant"],
            total_storm_cards=room["total_storm_cards"],
            max_clue_number=room["max_clue_number"],
        )

        for player in room["players"]:
            self.update_player_status(player, "Spielt")

        self.logger.info("START_GAME event after logic initialization")
        initial_state = game_logic.get_current_state()
        room["game_logic"] = game_logic

        # Send game start message to all players in the room
        self.broadcast_to_room(
            room,
            {
                "type": "game_start",
                "room_name": room_name,
                "players": room["players"],
                "initial_state": initial_state,
                "host": room["host"],
                "variant": room["variant"],
                "total_storm_cards": room["total_storm_cards"],
                "max_clue_number": room["max_clue_number"],
            },
        )
        self.broadcast()

    def handle_game_update(self, client_info, data):
        room_name = data.get("room_name")
        game_state = data.get("game_state")

        if not game_state:
            self.logger.error(f"Received empty game state update for room {room_name}")
            return

        self.logger.info(
            f"Received game update from {client_info['name']} in {room_name}"
        )

        room = next((r for r in self.rooms if r["room_name"] == room_name), None)
        if not room:
            self.logger.warning(f"Game update failed: Room {room_name} not found")
            return
        if room["status"] != "spielt":
            self.logger.warning(
                f"Game update ignored: Room {room_name} is not in playing state"
            )
            return

        try:
            room["game_logic"].update_state(game_state)

        except Exception as e:
            self.logger.error(f"Error updating game state: {e}")
            return

        # Boardcast game state update
        self.broadcast_to_room(room, {"type": "game_update", "game_state": game_state})
        self.logger.info(f"Broadcasted updated game state: {game_state}")

    def update_player_status(self, player_name, new_status):
        # Update player status
        for player in self.players:
            if player["name"] == player_name:
                player["status"] = new_status
                break

    def broadcast_to_room(self, room, data):
        for player_name in room["players"]:
            client = next((c for c in self.clients if c["name"] == player_name), None)
            if client:
                try:
                    client["socket"].sendall(pickle.dumps(data))
                    self.logger.info(
                        f"Broadcasted to {player_name} in room '{room['room_name']}'"
                    )
                except Exception as e:
                    self.logger.error(f"Room broadcast error: {e}")
                    self.disconnect_client(client["socket"])

    def broadcast_game_state(self, room):
        game_logic = room["game_logic"]
        game_state = game_logic.get_full_game_state()

        if not game_state:
            self.logger.error(f"Game state is empty for room {room['room_name']}")
            return

        self.logger.info(f"Broadcasting game state: {game_state}")

        message = {"type": "game_update", "game_state": game_state}

        for client_info in room["players"]:
            try:
                client_socket = client_info["socket"]
                serialized_data = pickle.dumps(message)
                client_socket.sendall(serialized_data)
                self.logger.info(f"Sent game update to {client_info['name']}")
            except (ConnectionResetError, BrokenPipeError) as e:
                self.logger.error(
                    f"Failed to send game state to {client_info['name']}: {e}"
                )


if __name__ == "__main__":
    print("Welcome to Hanabi Server Setup!")

    # read config.json
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            config = json.load(file)
        default_host = config["server"].get("host", "0.0.0.0")
        default_port = config["server"].get("port", 12345)
    else:
        default_host = "0.0.0.0"
        default_port = 12345

    # Allow the user to enter the IP and port; if left blank, use the values from config.json
    host_input = input(
        "Enter the IP address to bind the server to (or press enter to use config.json): "
    ).strip()
    port_input = input(
        "Enter the port number (or press enter to use config.json): "
    ).strip()

    host = host_input if host_input else default_host
    port = int(port_input) if port_input.isdigit() else default_port

    server = HanabiServer(host, port)
    print(f"Server is running on {server.host}:{server.port}. You can now connect!")
    server.start()
