import pygame
import sys
import os
import logging

from gui.login import LoginPage
from gui.lobby import GameListPage
from gui.newgame import NewGamePage
from gui.waiting import WaitingPage
from gui.help import HelpPage
from gui.ingame import GamingPage


class Application:
    def __init__(self, client):
        self.logger = logging.getLogger(__name__)
        # parameters
        self.screen_width, self.screen_height = 1200, 800
        self.darkgreen = 100, 150, 100

        self.client = client
        self.client.set_callback("lobby_update", self.update_lobby)
        self.client.set_callback("room_update", self.update_waiting_page)
        self.client.set_callback("game_start", self.start_game)
        if self.client.connected:
            self.client.auto_refresh_lobby()

        os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Hanabi")

        self.current_page = "login"
        self.transitioning = False

        self.login_page = LoginPage(self.client)
        self.game_list_page = None
        self.new_game_page = None
        self.waiting_page = None
        self.help_page = None
        self.gaming_page = None

    def update_lobby(self):
        if self.current_page == "game_list" and self.game_list_page:
            self.client.send_message("get_lobby_update")
            pygame.time.delay(100)
            self.game_list_page.render()

    def update_waiting_page(self, room_info):
        if self.current_page == "waiting" and self.waiting_page:
            self.waiting_page.update_info(room_info)
            self.waiting_page.render()

    def start_game(self, game_logic):
        self.logger.info(f"Starting game with logic: {game_logic}")  # Debug log
        try:
            self.gaming_page = GamingPage(game_logic, self.client)
            self.current_page = "gaming"
            self.transitioning = False
            self.logger.info("Game page initialized successfully")
        except Exception as e:
            self.logger.error(f"Error starting game: {e}")
            import traceback

            logging.error("An exception occurred:\n%s", traceback.format_exc())

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            self.screen.fill(self.darkgreen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    if self.client:
                        self.client.disconnect()

                if not self.transitioning:
                    if self.current_page == "login":
                        action = self.login_page.handle_event(event)
                        if action == "lobby":
                            self.game_list_page = GameListPage(self.client)
                            self.current_page = "game_list"
                        elif action == "quit":
                            running = False

                    elif self.current_page == "game_list":
                        action = self.game_list_page.handle_event(event)
                        if action == "Neues Spiel" or action == "New Game":
                            self.new_game_page = NewGamePage(self.client)
                            self.current_page = "new_game"
                        elif action == "Abmelden" or action == "Sign Out":
                            self.login_page = LoginPage(self.client)
                            self.current_page = "login"
                        elif action == "Hilfe" or action == "Help":
                            self.help_page = HelpPage(self.client)
                            self.current_page = "help"
                        elif isinstance(action, dict):
                            self.waiting_page = WaitingPage(self.client, action)
                            self.current_page = "waiting"

                    elif self.current_page == "new_game":
                        action = self.new_game_page.handle_event(event)
                        if action == "back":
                            self.game_list_page = GameListPage(self.client)
                            self.current_page = "game_list"
                        elif isinstance(action, dict):
                            self.waiting_page = WaitingPage(self.client, action)
                            self.current_page = "waiting"

                    elif self.current_page == "waiting":
                        action = self.waiting_page.handle_event(event)
                        if action == "exit":
                            self.game_list_page = GameListPage(self.client)
                            self.current_page = "game_list"
                        elif action == "game_start":
                            self.transitioning = True
                            room_name = self.waiting_page.game_info["room_name"]
                            self.client.start_game(room_name)

                    elif self.current_page == "help":
                        action = self.help_page.handle_event(event)
                        if action == "back":
                            self.game_list_page = GameListPage(self.client)
                            self.current_page = "game_list"

                    elif self.current_page == "gaming":
                        if self.gaming_page:
                            result = self.gaming_page.handle_event(event)
                            if result == "exit":
                                # Reset game page when exiting
                                self.gaming_page = None
                                # Refresh the game list page with new state
                                self.game_list_page = GameListPage(self.client)
                                self.current_page = "game_list"
                                # Request a lobby update to refresh the game list
                                self.client.send_message("get_lobby_update")

                                # Render the current page
            try:
                if self.current_page == "login":
                    self.login_page.render()
                elif self.current_page == "game_list":
                    self.game_list_page.render()
                elif self.current_page == "new_game":
                    self.new_game_page.render()
                elif self.current_page == "waiting":
                    self.waiting_page.render()
                elif self.current_page == "help":
                    self.help_page.render()
                elif self.current_page == "gaming":
                    if self.gaming_page:
                        self.gaming_page.render()
            except Exception as e:
                self.logger.error(f"Render error: {e}")

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()
