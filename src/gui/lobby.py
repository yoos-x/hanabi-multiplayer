import pygame
import logging
import re


class GameListPage:
    def __init__(self, client):
        self.logger = logging.getLogger(__name__)

        # Parameters
        self.screen_width, self.screen_height = 1200, 800
        self.darkgreen = 100, 150, 100
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        self.client = client
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.is_german = self.client.is_german

        # Toolbar buttons
        self.toolbar_buttons = {
            "Neues Spiel": pygame.Rect(100, 10, 150, 30),
            "Sprache": pygame.Rect(350, 10, 150, 30),
            "Hilfe": pygame.Rect(600, 10, 150, 30),
            "Abmelden": pygame.Rect(850, 10, 150, 30),
        }
        self.columns = ["Spiel", "Spieler", "Variante", "Status"]
        self.language_menu = {
            "Deutsch": pygame.Rect(350, 50, 150, 30),
            "Englisch": pygame.Rect(350, 90, 150, 30),
        }
        self.language_menu_visible = False

        # Chat related
        self.chat_input_box = pygame.Rect(50, 700, 700, 40)
        self.chat_input_text = ""
        self.is_typing = False

        # Join game buttons
        self.join_buttons = []

    def update_user_list(self):
        self.client.send_message("get_lobby_update")
        pygame.time.delay(100)
        self.render()  # force rerender userlist

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.update_user_list()
            # Click toolbar buttons
            for button_name, button_rect in self.toolbar_buttons.items():
                if button_rect.collidepoint(event.pos):
                    self.logger.info(f"{button_name} button clicked!")
                    if button_name == "Abmelden" or button_name == "Sign Out":
                        self.client.disconnect()  # disconnected
                        self.client.send_message(
                            "get_lobby_update"
                        )  # force lobbyupdate
                        self.render()  # rerender
                    if button_name == "Sprache" or button_name == "Language":
                        self.language_menu_visible = not self.language_menu_visible
                    return button_name

            if self.language_menu_visible:
                for language, rect in self.language_menu.items():
                    if rect.collidepoint(event.pos):
                        self.is_german = language == "Deutsch" or language == "German"
                        self.language_menu_visible = False
                        self.client.is_german = self.is_german
                        self.render()
                        return language

            # Click join game button
            for button_rect, game_index in self.join_buttons:
                if button_rect.collidepoint(event.pos):
                    game = self.client.games[game_index]
                    self.logger.info(f"Joining {game['room_name']}...")
                    self.client.join_game(game["room_name"])
                    return game

            # Click chat input box
            if self.chat_input_box.collidepoint(event.pos):
                self.is_typing = True
            else:
                self.is_typing = False

        elif event.type == pygame.KEYDOWN and self.is_typing:
            if event.key == pygame.K_RETURN and self.chat_input_text.strip():
                self.client.logger.info(
                    f"Attempting to send message: {self.chat_input_text.strip()}"
                )
                self.client.send_message(
                    "chat",
                    name=self.client.username,
                    message=self.chat_input_text.strip(),
                )
                self.chat_input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.chat_input_text = self.chat_input_text[:-1]
            else:
                self.chat_input_text += event.unicode
        return None

    def render(self):
        self.screen.fill(self.darkgreen)
        self.join_buttons = []

        if self.is_german:
            self.toolbar_buttons = {
                "Neues Spiel": pygame.Rect(100, 10, 150, 30),
                "Sprache": pygame.Rect(350, 10, 150, 30),
                "Hilfe": pygame.Rect(600, 10, 150, 30),
                "Abmelden": pygame.Rect(850, 10, 150, 30),
            }
            self.columns = ["Spiel", "Spieler", "Variante", "Status"]
            self.language_menu = {
                "Deutsch": pygame.Rect(350, 50, 150, 30),
                "Englisch": pygame.Rect(350, 90, 150, 30),
            }
        else:
            self.toolbar_buttons = {
                "New Game": pygame.Rect(100, 10, 150, 30),
                "Language": pygame.Rect(350, 10, 150, 30),
                "Help": pygame.Rect(600, 10, 150, 30),
                "Sign Out": pygame.Rect(850, 10, 150, 30),
            }
            self.columns = ["Game", "Players", "Variant", "Status"]
            self.language_menu = {
                "German": pygame.Rect(350, 50, 150, 30),
                "English": pygame.Rect(350, 90, 150, 30),
            }

        # Draw toolbar buttons
        for button_name, button_rect in self.toolbar_buttons.items():
            pygame.draw.rect(self.screen, (50, 50, 50), button_rect)
            text_surface = self.font.render(button_name, True, "white")
            text_x = button_rect.x + (button_rect.width - text_surface.get_width()) // 2
            text_y = (
                button_rect.y + (button_rect.height - text_surface.get_height()) // 2
            )
            self.screen.blit(text_surface, (text_x, text_y))

        # Draw game list title
        pygame.draw.rect(self.screen, "white", (50, 80, 700, 280))
        header_text = "Spielliste" if self.is_german else "List of Games"
        header_surface = self.font.render(header_text, True, "black")
        self.screen.blit(header_surface, (50, 50))

        # Draw column titles
        for i, col in enumerate(self.columns):
            col_surface = self.small_font.render(col, True, "black")
            self.screen.blit(col_surface, (60 + i * 150, 90))
        pygame.draw.line(self.screen, self.darkgreen, (50, 115), (750, 115), 4)

        # Draw game list content
        for row_index, game in enumerate(self.client.games):
            if game["status"] == "spielt":
                lobby_status = "Spiel läuft" if self.is_german else "Playing"
            elif game["status"] == "warten":
                lobby_status = "Wartend" if self.is_german else "Waiting"
            elif game["status"] == "In Lobby":
                lobby_status = "In der Lobby" if self.is_german else "In Lobby"

            row_y = 140 + row_index * 40
            players_number = f"{len(game['players'])}/{game['max_players']}"
            game_values = [
                game["room_name"],
                players_number,
                game["variant"],
                lobby_status,
            ]
            for col_index, value in enumerate(game_values):
                value_surface = self.small_font.render(str(value), True, "black")
                self.screen.blit(value_surface, (60 + col_index * 150, row_y))

            # Draw Join button
            if (
                game["status"] == "warten"
                and len(game["players"]) < game["max_players"]
            ):
                join_button_rect = pygame.Rect(650, row_y - 10, 90, 30)
                self.join_buttons.append((join_button_rect, row_index))
                pygame.draw.rect(self.screen, (0, 200, 0), join_button_rect)
                join_text = "Beitreten" if self.is_german else "Join"
                join_surface = self.small_font.render(join_text, True, "white")
                join_text_x = (
                    join_button_rect.x
                    + (join_button_rect.width - join_surface.get_width()) // 2
                )
                join_text_y = (
                    join_button_rect.y
                    + (join_button_rect.height - join_surface.get_height()) // 2
                )
                self.screen.blit(join_surface, (join_text_x, join_text_y))

        # Draw chat windows
        pygame.draw.rect(self.screen, "white", (50, 410, 700, 280))
        chat_header_text = "Lobby Chat" if self.is_german else "Lobby Chat"
        chat_header_surface = self.font.render(chat_header_text, True, "black")
        self.screen.blit(chat_header_surface, (50, 380))

        # Draw chat history
        for i, message in enumerate(self.client.chat_history[-10:]):
            chat_surface = self.small_font.render(
                f"{message['name']}: {message['message']}", True, "black"
            )
            self.screen.blit(chat_surface, (60, 420 + i * 30))

        # Draw chat input box
        pygame.draw.rect(self.screen, "white", self.chat_input_box)
        input_text = self.small_font.render(self.chat_input_text, True, "black")
        self.screen.blit(
            input_text, (self.chat_input_box.x + 5, self.chat_input_box.y + 10)
        )

        # Draw online user list
        pygame.draw.rect(self.screen, "white", (800, 80, 350, 620))
        user_header_text = "Onlinenutzer" if self.is_german else "Online Users"
        user_header_surface = self.font.render(user_header_text, True, "black")
        self.screen.blit(user_header_surface, (800, 50))
        for i, user in enumerate(self.client.online_users):
            if user["status"] == "Spielt":
                lobby_status = "Spiel läuft" if self.is_german else "Playing"
            elif user["status"] == "warten":
                lobby_status = "Warten" if self.is_german else "Waiting"
            elif user["status"] == "In Lobby":
                lobby_status = "In der Lobby" if self.is_german else "In Lobby"
            elif re.match(r"^In Raum: ", user["status"]):
                lobby_status = (
                    re.sub(r"^In Raum", "Im Raum", game["status"])
                    if self.is_german
                    else game["status"]
                )
            else:
                lobby_status = game["status"]

            user_text = f"{user['name']} - {lobby_status}"
            user_surface = self.small_font.render(user_text, True, "black")
            self.screen.blit(user_surface, (810, 90 + i * 30))

        if self.language_menu_visible:
            for language, rect in self.language_menu.items():
                pygame.draw.rect(self.screen, (50, 50, 50), rect)
                lang_surface = self.font.render(language, True, "white")
                text_x = rect.x + (rect.width - lang_surface.get_width()) // 2
                text_y = rect.y + (rect.height - lang_surface.get_height()) // 2
                self.screen.blit(lang_surface, (text_x, text_y))
