import pygame
import logging


class WaitingPage:
    def __init__(self, client, game_info):
        self.logger = logging.getLogger(__name__)
        self.client = client
        self.is_german = self.client.is_german

        # parameters
        self.small_width, self.small_height = 1200, 800
        self.title_font = pygame.font.Font(None, 40)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

        self.screen = pygame.display.set_mode((self.small_width, self.small_height))

        self.game_info = game_info
        self.is_host = game_info["host"] == client.username

        # Buttons
        self.exit_button = pygame.Rect(300, 700, 150, 40)
        self.start_button = pygame.Rect(700, 700, 159, 40)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Exit button
            if self.exit_button.collidepoint(event.pos):
                self.client.leave_game(self.game_info["room_name"])
                self.logger.info("Returning to the game list page...")
                return "exit"

            # Start button
            if self.start_button.collidepoint(event.pos) and self.is_host:
                if len(self.game_info["players"]) == self.game_info["max_players"]:
                    self.logger.info(f"{self.game_info['room_name']} starts!")
                    return "game_start"
                else:
                    self.logger.info(
                        "The number of players does not match the target number!"
                    )
        return None

    def update_info(self, new_info):
        # Update game room information
        self.game_info = new_info
        self.is_host = new_info["host"] == self.client.username
        self.logger.info(f"Updated WaitingPage with new info: {new_info}")

    def render(self):
        self.screen.fill("white")

        # Title
        title_text = "Warte Raum" if self.is_german else "Waiting Room"
        title = self.title_font.render(
            f"{title_text} - {self.game_info['room_name']}", True, "black"
        )
        title_width = title.get_width()
        center_x = (self.small_width - title_width) // 2
        self.screen.blit(title, (center_x, 50))

        # details texts in different languages
        text_variant = "Variante" if self.is_german else "Variant"
        text_players = "Spieler" if self.is_german else "Players"
        text_number_of_storm_cards = (
            "Anzahl der Gewitterkarten" if self.is_german else "Number of storm cards"
        )
        text_number_of_clues = (
            "Anzahl der Hinweise" if self.is_german else "Number of clues"
        )
        text_player_list = "Spielerliste" if self.is_german else "Player list"

        # Display game details
        details = [
            f"{text_variant}: {self.game_info['variant']}",
            f"{text_players}: {len(self.game_info['players'])}/{self.game_info['max_players']}",
            f"{text_number_of_storm_cards}: {self.game_info['total_storm_cards']}",
            f"{text_number_of_clues}: {self.game_info['max_clue_number']}",
            f"{text_player_list}:",
        ]

        for i, label in enumerate(details):
            label_surface = self.font.render(label, True, "black")
            self.screen.blit(label_surface, (300, 160 + i * 60))

        # Player list
        for i, player in enumerate(self.game_info["players"]):
            player_text = f"- {player}"
            if player == self.game_info["host"]:
                player_text += " (Host)"
            player_surface = self.font.render(player_text, True, "black")
            self.screen.blit(player_surface, (350, 450 + i * 30))

        # Buttons
        pygame.draw.rect(self.screen, (200, 50, 50), self.exit_button)
        exit_text = "Beenden" if self.is_german else "Exit"
        exit_surface = self.small_font.render(exit_text, True, "white")
        self.screen.blit(
            exit_surface, (self.exit_button.x + 50, self.exit_button.y + 10)
        )

        if (
            self.is_host
            and len(self.game_info["players"]) == self.game_info["max_players"]
        ):
            pygame.draw.rect(self.screen, (50, 200, 50), self.start_button)
            start_surface = self.small_font.render("Start", True, "white")
        else:
            pygame.draw.rect(self.screen, (100, 100, 100), self.start_button)
            start_text = "Warten..." if self.is_german else "Waiting..."
            start_surface = self.small_font.render(start_text, True, "white")
        self.screen.blit(
            start_surface, (self.start_button.x + 50, self.start_button.y + 10)
        )
