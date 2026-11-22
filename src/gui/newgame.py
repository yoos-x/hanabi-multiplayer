import pygame
import logging


class NewGamePage:
    def __init__(self, client):
        self.logger = logging.getLogger(__name__)
        self.client = client
        self.is_german = self.client.is_german

        # Parameters
        self.small_width, self.small_height = 800, 800
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 40)

        self.background_color = 240, 240, 240

        self.screen = pygame.display.set_mode((self.small_width, self.small_height))
        self.back_button = pygame.Rect(100, 700, 150, 40)
        self.create_button = pygame.Rect(500, 700, 159, 40)

        # Input fields for name
        self.name_input = pygame.Rect(250, 150, 450, 40)

        # variant options texts in different languages
        text_no_variant = "Keine Variante" if self.is_german else "No variant"
        text_fireworks = "Farbrausch" if self.is_german else "Multicolor"

        # Dropdown menu for "Variant"
        self.variant_dropdown = pygame.Rect(250, 250, 450, 40)
        self.variant_options = [
            text_no_variant,
            text_fireworks,
        ]
        self.variant_selected = text_no_variant
        self.variant_dropdown_open = False

        # Dropdown menu for "Number of Players"
        self.player_numbers_dropdown = pygame.Rect(250, 350, 450, 40)
        self.player_numbers_options = ["2", "3", "4", "5"]
        self.player_numbers_selected = "4"
        self.player_numbers_dropdown_open = False

        # Dropdown menu for "Storm Cards"
        self.storm_cards_dropdown = pygame.Rect(250, 450, 450, 40)
        self.storm_cards_options = ["1", "2", "3"]
        self.storm_cards_selected = "3"
        self.storm_cards_dropdown_open = False

        # Input fields for hints
        self.hints_input = pygame.Rect(250, 550, 450, 40)

        # Input field states
        self.active_input = None
        self.name_text = ""
        self.hints_text = "8"

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Back button
            if self.back_button.collidepoint(event.pos):
                self.logger.info("Returning to the game list page...")
                return "back"

            # Create button
            if self.create_button.collidepoint(event.pos):
                if not self.name_text.strip():
                    self.logger.info("Please enter a game name!")
                else:
                    self.logger.info(f"Creating game: {self.name_text}!")
                    self.client.create_game(
                        room_name=self.name_text,
                        max_players=int(self.player_numbers_selected),
                        variant=self.variant_selected,
                        total_storm_cards=int(self.storm_cards_selected),
                        max_clue_number=int(self.hints_text.strip())
                        if self.hints_text.strip().isdigit()
                        else 8,
                    )
                    return {
                        "room_name": self.name_text,
                        "players": [self.client.username],
                        "max_players": int(self.player_numbers_selected),
                        "variant": self.variant_selected,
                        "total_storm_cards": int(self.storm_cards_selected),
                        "max_clue_number": int(self.hints_text.strip())
                        if self.hints_text.strip().isdigit()
                        else 8,
                        "status": "waiting",
                        "host": self.client.username,
                    }

            # Check if input fields are clicked
            if self.name_input.collidepoint(event.pos):
                self.active_input = "name"
            elif (
                self.hints_input.collidepoint(event.pos)
                and not self.variant_dropdown_open
                and not self.player_numbers_dropdown_open
                and not self.storm_cards_dropdown_open
            ):
                self.active_input = "hints"
            else:
                self.active_input = None

            # Variant dropdown menu interaction
            if self.variant_dropdown.collidepoint(event.pos):
                self.variant_dropdown_open = not self.variant_dropdown_open
                self.player_numbers_dropdown_open = False
                self.storm_cards_dropdown_open = False
            elif self.variant_dropdown_open:
                for i, option in enumerate(self.variant_options):
                    option_rect = pygame.Rect(250, 300 + i * 40, 450, 40)
                    if option_rect.collidepoint(event.pos):
                        self.variant_selected = option
                        self.variant_dropdown_open = False
                        break
                else:
                    self.variant_dropdown_open = False

            # Players dropdown menu interaction
            if self.player_numbers_dropdown.collidepoint(event.pos):
                self.player_numbers_dropdown_open = (
                    not self.player_numbers_dropdown_open
                )
                self.variant_dropdown_open = False
                self.storm_cards_dropdown_open = False
            elif self.player_numbers_dropdown_open:
                for i, option in enumerate(self.player_numbers_options):
                    option_rect = pygame.Rect(250, 400 + i * 40, 450, 40)
                    if option_rect.collidepoint(event.pos):
                        self.player_numbers_selected = option
                        self.player_numbers_dropdown_open = False
                        break
                else:
                    self.player_numbers_dropdown_open = False

            # Storm Cards dropdown menu interaction
            if self.storm_cards_dropdown.collidepoint(event.pos):
                self.storm_cards_dropdown_open = not self.storm_cards_dropdown_open
                self.variant_dropdown_open = False
                self.player_numbers_dropdown_open = False
            elif self.storm_cards_dropdown_open:
                for i, option in enumerate(self.storm_cards_options):
                    option_rect = pygame.Rect(250, 490 + i * 40, 450, 40)
                    if option_rect.collidepoint(event.pos):
                        self.storm_cards_selected = option
                        self.storm_cards_dropdown_open = False
                        break
                else:
                    self.storm_cards_dropdown_open = False

        if event.type == pygame.KEYDOWN and self.active_input:
            if self.active_input == "name":
                if event.key == pygame.K_BACKSPACE:
                    self.name_text = self.name_text[:-1]
                else:
                    self.name_text += event.unicode
            if self.active_input == "hints":
                if event.key == pygame.K_BACKSPACE:
                    self.hints_text = self.hints_text[:-1]
                elif event.unicode.isdigit():
                    # Hints input only allows numbers
                    self.hints_text += event.unicode
        return None

    def render(self):
        self.screen.fill("white")

        # Title
        title_text = (
            "Erstelle ein neues Spiel" if self.is_german else "Create a new game"
        )
        title = self.title_font.render(title_text, True, "black")
        title_width = title.get_width()
        center_x = (self.small_width - title_width) // 2
        self.screen.blit(title, (center_x, 50))

        # labels
        labels = ["Name:", "Variante:"] if self.is_german else ["Name:", "Variant:"]
        for i, label in enumerate(labels):
            label_surface = self.small_font.render(label, True, "black")
            self.screen.blit(label_surface, (100, 160 + i * 100))
        number_of_players_lines = (
            ["Anzahl der", "Spieler:"] if self.is_german else ["Number of", "players:"]
        )
        for i, line in enumerate(number_of_players_lines):
            line_surface = self.small_font.render(line, True, "black")
            self.screen.blit(line_surface, (100, 355 + i * 20))

        number_of_storm_cards_lines = (
            ["Anzahl der", "Gewitterkarten:"]
            if self.is_german
            else ["Number of", "storm cards"]
        )
        for i, line in enumerate(number_of_storm_cards_lines):
            line_surface = self.small_font.render(line, True, "black")
            self.screen.blit(line_surface, (100, 455 + i * 20))

        number_of_hints_lines = (
            ["Anzahl der", "Hinweise:"] if self.is_german else ["Number of", "clues:"]
        )
        for i, line in enumerate(number_of_hints_lines):
            line_surface = self.small_font.render(line, True, "black")
            self.screen.blit(line_surface, (100, 555 + i * 20))

        # Name Input fields
        pygame.draw.rect(
            self.screen,
            "black",
            self.name_input,
            2 if self.active_input == "name" else 1,
        )
        name_surface = self.small_font.render(self.name_text, True, "black")
        self.screen.blit(name_surface, (self.name_input.x + 5, self.name_input.y + 10))

        # Hints Input Field
        if not self.storm_cards_dropdown_open and not self.player_numbers_dropdown_open:
            pygame.draw.rect(
                self.screen,
                "black",
                self.hints_input,
                2 if self.active_input == "hints" else 1,
            )
            hints_surface = self.small_font.render(self.hints_text, True, "black")
            self.screen.blit(
                hints_surface, (self.hints_input.x + 5, self.hints_input.y + 10)
            )

        # Variant field
        pygame.draw.rect(
            self.screen,
            "black",
            self.variant_dropdown,
            2 if self.variant_dropdown_open == True else 1,
        )
        variant_surface = self.small_font.render(self.variant_selected, True, "black")
        self.screen.blit(
            variant_surface, (self.variant_dropdown.x + 5, self.variant_dropdown.y + 10)
        )

        # Players field
        pygame.draw.rect(
            self.screen,
            "black",
            self.player_numbers_dropdown,
            2 if self.player_numbers_dropdown_open == True else 1,
        )
        player_numbers_surface = self.small_font.render(
            self.player_numbers_selected, True, "black"
        )
        self.screen.blit(
            player_numbers_surface,
            (self.player_numbers_dropdown.x + 5, self.player_numbers_dropdown.y + 10),
        )

        # Storm Cards field
        pygame.draw.rect(
            self.screen,
            "black",
            self.storm_cards_dropdown,
            2 if self.storm_cards_dropdown_open else 1,
        )
        storm_cards_surface = self.small_font.render(
            self.storm_cards_selected, True, "black"
        )
        self.screen.blit(
            storm_cards_surface,
            (self.storm_cards_dropdown.x + 5, self.storm_cards_dropdown.y + 10),
        )

        # Variant dropdown menu
        if self.variant_dropdown_open:
            for i, option in enumerate(self.variant_options):
                option_rect = pygame.Rect(250, 300 + i * 40, 450, 40)
                pygame.draw.rect(self.screen, self.background_color, option_rect)
                option_surface = self.small_font.render(option, True, (0, 0, 0))
                self.screen.blit(
                    option_surface, (option_rect.x + 5, option_rect.y + 10)
                )

        # Players dropdown menu
        if self.player_numbers_dropdown_open:
            for i, option in enumerate(self.player_numbers_options):
                option_rect = pygame.Rect(250, 400 + i * 40, 450, 40)
                pygame.draw.rect(self.screen, self.background_color, option_rect)
                option_surface = self.small_font.render(option, True, (0, 0, 0))
                self.screen.blit(
                    option_surface, (option_rect.x + 5, option_rect.y + 10)
                )

        # Storm Cards Dropdown
        if self.storm_cards_dropdown_open:
            for i, option in enumerate(self.storm_cards_options):
                option_rect = pygame.Rect(250, 490 + i * 40, 450, 40)
                pygame.draw.rect(self.screen, self.background_color, option_rect)
                option_surface = self.small_font.render(option, True, (0, 0, 0))
                self.screen.blit(
                    option_surface, (option_rect.x + 5, option_rect.y + 10)
                )

        # Buttons
        pygame.draw.rect(self.screen, (200, 50, 50), self.back_button)
        back_text = "Zurück" if self.is_german else "Back"
        back_surface = self.small_font.render(back_text, True, "white")
        self.screen.blit(
            back_surface, (self.back_button.x + 50, self.back_button.y + 10)
        )

        pygame.draw.rect(self.screen, (50, 200, 50), self.create_button)
        create_text = "Starten" if self.is_german else "Starting"
        create_surface = self.small_font.render(create_text, True, "white")
        self.screen.blit(
            create_surface, (self.create_button.x + 50, self.create_button.y + 10)
        )
