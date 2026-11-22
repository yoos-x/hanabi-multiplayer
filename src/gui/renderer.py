import pygame
import re

# Global Constants
# screen dimensions
WIDTH, HEIGHT = 1200, 800

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
SELECTED_COLOR = (0, 255, 0)
CARD_COLORS = {
    "Red": {"bg": (180, 80, 80), "text": WHITE},
    "Yellow": {"bg": (200, 180, 100), "text": WHITE},
    "Green": {"bg": (100, 150, 100), "text": WHITE},
    "Blue": {"bg": (80, 130, 180), "text": WHITE},
    "Purple": {"bg": (140, 100, 160), "text": WHITE},
    "Orange": {"bg": (230, 120, 20), "text": WHITE},
}

HINTED_CARD_COLORS = {
    "Red": {"bg": (255, 50, 50), "text": BLACK},
    "Yellow": {"bg": (255, 255, 100), "text": BLACK},
    "Green": {"bg": (50, 255, 50), "text": BLACK},
    "Blue": {"bg": (50, 100, 255), "text": BLACK},
    "Purple": {"bg": (150, 50, 255), "text": BLACK},
    "Orange": {"bg": (255, 100, 0), "text": BLACK},
}

# Card settings
CARD_WIDTH, CARD_HEIGHT = 60, 90
CARD_SPACING = 20
PLAYER_SPACING = CARD_HEIGHT + CARD_SPACING
NAME_WIDTH = 80

SQUARE_SIZE = 40
RECT_WIDTH = 120
RECT_HEIGHT = 40
CLUE_X = WIDTH - 20 - 5 * (SQUARE_SIZE + CARD_SPACING)
CLUE_Y = 30

FIREWORK_X = 30
FIREWORK_Y = HEIGHT - 70 - CARD_HEIGHT
TRASH_X = FIREWORK_X + 5 * (CARD_WIDTH + CARD_SPACING) + 2 * CARD_SPACING
TRASH_Y = FIREWORK_Y

LOG_BOX_X = 550
LOG_BOX_Y = 480
LOG_BOX_WIDTH = 630
LOG_BOX_HEIGHT = 250

INFO_BOX_X = 550
INFO_BOX_Y = 10
INFO_BOX_WIDTH = 300
INFO_BOX_HEIGHT = 260

STORM_X = 550
STORM_Y = 300


class Renderer:
    def __init__(self, screen, client):
        self.screen = screen
        self.client = client
        self.is_german = self.client.is_german

        # fonts
        self.font = pygame.font.SysFont("Arial", 24)
        self.number_font = pygame.font.SysFont("arialblack", 32)
        self.small_font = pygame.font.SysFont("Arial", 22)
        self.scroll_offset = 0

    # Function to draw cards

    def draw_card(
        self, x, y, value, color, hide_value=False, selected=False, hinted=None
    ):
        # Background
        if selected:
            pygame.draw.rect(
                self.screen,
                SELECTED_COLOR,
                (x - 5, y - 5, CARD_WIDTH + 10, CARD_HEIGHT + 10),
            )
        if hide_value:
            if hinted and "color" in hinted:
                card_color = HINTED_CARD_COLORS[hinted["color"]]["bg"]
            else:
                card_color = GRAY
        else:
            if hinted and "color" in hinted:
                card_color = HINTED_CARD_COLORS[hinted["color"]]["bg"]
            else:
                card_color = CARD_COLORS[color]["bg"]
        pygame.draw.rect(self.screen, card_color, (x, y, CARD_WIDTH, CARD_HEIGHT))

        # Text
        text_color = None
        if hide_value:
            if hinted and "number" in hinted:
                text_color = HINTED_CARD_COLORS[color]["text"]
        else:
            if hinted and "number" in hinted:
                text_color = HINTED_CARD_COLORS[color]["text"]
            else:
                text_color = CARD_COLORS[color]["text"]
        if text_color:
            text = self.number_font.render(str(value), True, text_color)
            text_rect = text.get_rect(
                center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
            )
            self.screen.blit(text, text_rect)

    # Function to draw fireworks
    def draw_fireworks(self, x, y, value, color, selected=False):
        card_color = CARD_COLORS[color]
        if selected:
            pygame.draw.rect(
                self.screen,
                SELECTED_COLOR,
                (x - 5, y - 5, CARD_WIDTH + 10, CARD_HEIGHT + 10),
            )
        if value == 0:
            pygame.draw.rect(
                self.screen, card_color["bg"], (x, y, CARD_WIDTH, CARD_HEIGHT)
            )
            pygame.draw.rect(self.screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)
        else:
            pygame.draw.rect(
                self.screen, card_color["bg"], (x, y, CARD_WIDTH, CARD_HEIGHT)
            )
            pygame.draw.rect(self.screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)
            text = self.number_font.render(str(value), True, card_color["text"])
            text_rect = text.get_rect(
                center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
            )
            self.screen.blit(text, text_rect)

    # funkcion to wrap a text
    def wrap_text(self, text, font, max_width):
        if not text.strip():
            return []

        words = text.split(" ")
        wrapped_lines = []
        current_line = []
        current_width = 0
        for word in words:
            word_width, _ = font.size(word + " ")
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                wrapped_lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            wrapped_lines.append(" ".join(current_line))
        return wrapped_lines

    # funktion to scroll the logs
    def scroll_logs(self, direction):
        self.scroll_offset += direction
        self.scroll_offset = max(
            0, min(self.scroll_offset, self.max_scroll)
        )  # Limitation

    # Function to draw log and diacard pile button
    def draw_log_discard_buttons(self):
        log_button_label = "Protokolle" if self.is_german else "Logs"
        discard_pile_label = "Ablagestapel" if self.is_german else "Discard Pile"

        self.draw_shape(881, LOG_BOX_Y - 29, 150, 30, WHITE, log_button_label, BLACK)
        self.draw_shape(
            1030, LOG_BOX_Y - 29, 150, 30, "lightgray", discard_pile_label, BLACK
        )
        pygame.draw.rect(
            self.screen, BLACK, (LOG_BOX_X, LOG_BOX_Y, LOG_BOX_WIDTH, LOG_BOX_HEIGHT), 3
        )

    def translation_logs(self, log, is_german):
        if not log:
            return log

        if is_german:
            translations = {
                "Red": "Rot",
                "Yellow": "Gelb",
                "Green": "Grün",
                "Blue": "Blau",
                "Purple": "Lila",
            }
        else:
            translations = {
                r"Ungültige Aktion:": "Invalid action:",
                r"versucht eine ungültige Karte zu spielen\.": "attempted to play an invalid card.",
                r"spielt erfolgreich eine": "successfully plays a",
                r"von der Stelle": "from position",
                r"auf die": "onto the",
                r"Feuerwerke!": "fireworks!",
                r"Ihr gewinnt das Spiel!": "You win the game!",
                r"schlägt fehl eine": "fails to play a",
                r"zu spielen...": "to play...",
                r"Spiel vorbei - Keine Leben mehr übrig": "Game over - No lives left.",
                r"wirft": "discards",
                r"\bab\b": "",
                r"gibt": "gives",
                r"den Hinweis über die Karten mit der": "a hint about the cards with",
                r", es passen": "matches",
                r"Karte\(n\)": "card(s)",
                r"aber es wurden keine passenden Karten gefunden.": "but no matching cards were found.",
            }

        for german, english in translations.items():
            log = re.sub(german, english, log, flags=re.IGNORECASE)

        return log

    # Function to draw log box
    def draw_log_box(self, logs):
        # Draw log box border
        pygame.draw.rect(
            self.screen, BLACK, (LOG_BOX_X, LOG_BOX_Y, LOG_BOX_WIDTH, LOG_BOX_HEIGHT), 3
        )

        # Wrap text and prepare logs
        wrapped_logs = []
        for log in logs:
            translated_log = self.translation_logs(log, self.is_german)
            wrapped_logs.extend(
                self.wrap_text(translated_log, self.small_font, LOG_BOX_WIDTH - 40)
            )  # Reduced width for padding

        # Calculate visible lines
        line_height = 30
        max_visible_lines = (LOG_BOX_HEIGHT - 20) // line_height  # Account for padding
        total_lines = len(wrapped_logs)

        # Update scroll limits
        self.max_scroll = max(0, total_lines - max_visible_lines)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

        # Draw visible logs with scrolling
        visible_logs = wrapped_logs[
            max(0, self.scroll_offset) : max(0, self.scroll_offset) + max_visible_lines
        ]

        # Create a clipping rect for the log area
        clip_rect = pygame.Rect(
            LOG_BOX_X + 10, LOG_BOX_Y + 10, LOG_BOX_WIDTH - 20, LOG_BOX_HEIGHT - 20
        )
        self.screen.set_clip(clip_rect)

        # Draw logs
        for i, log in enumerate(visible_logs):
            text_surface = self.small_font.render(log, True, BLACK)
            text_x = LOG_BOX_X + 20  # Added padding
            text_y = (
                LOG_BOX_Y + 10 + i * line_height - self.scroll_offset * 2
            )  # Apply scroll offset
            self.screen.blit(text_surface, (text_x, text_y))

        # Reset clip
        self.screen.set_clip(None)

        # Draw scroll indicators
        pygame.draw.line(
            self.screen,
            "lightgray",
            (LOG_BOX_X + LOG_BOX_WIDTH - 30, LOG_BOX_Y + 10),
            (LOG_BOX_X + LOG_BOX_WIDTH - 30, LOG_BOX_Y + LOG_BOX_HEIGHT - 10),
            2,
        )
        if self.max_scroll > 0:
            if self.scroll_offset > 0:  # Can scroll up
                pygame.draw.polygon(
                    self.screen,
                    BLACK,
                    [
                        (LOG_BOX_X + LOG_BOX_WIDTH - 15, LOG_BOX_Y + 15),
                        (LOG_BOX_X + LOG_BOX_WIDTH - 25, LOG_BOX_Y + 25),
                        (LOG_BOX_X + LOG_BOX_WIDTH - 5, LOG_BOX_Y + 25),
                    ],
                )
            if self.scroll_offset < self.max_scroll:  # Can scroll down
                pygame.draw.polygon(
                    self.screen,
                    BLACK,
                    [
                        (
                            LOG_BOX_X + LOG_BOX_WIDTH - 15,
                            LOG_BOX_Y + LOG_BOX_HEIGHT - 15,
                        ),
                        (
                            LOG_BOX_X + LOG_BOX_WIDTH - 25,
                            LOG_BOX_Y + LOG_BOX_HEIGHT - 25,
                        ),
                        (
                            LOG_BOX_X + LOG_BOX_WIDTH - 5,
                            LOG_BOX_Y + LOG_BOX_HEIGHT - 25,
                        ),
                    ],
                )

    # Function to draw discard pile box
    def draw_discard_pile(self, discard_pile, fireworks):
        pygame.draw.rect(
            self.screen,
            "lightgray",
            (LOG_BOX_X, LOG_BOX_Y, LOG_BOX_WIDTH, LOG_BOX_HEIGHT),
        )
        pygame.draw.rect(
            self.screen, BLACK, (LOG_BOX_X, LOG_BOX_Y, LOG_BOX_WIDTH, LOG_BOX_HEIGHT), 3
        )

        def translate_color(color, is_german):
            if not is_german:
                return color
            else:
                return (
                    "Rot"
                    if color == "Red"
                    else "Gelb"
                    if color == "Yellow"
                    else "Grün"
                    if color == "Green"
                    else "Blau"
                    if color == "Blue"
                    else "Lila"
                    if color == "Purple"
                    else color
                )

        active_colors = [color for _, color in fireworks]
        discard_dict = {color: [] for color in active_colors}
        for value, color in discard_pile:
            discard_dict[color].append(value)
        for i, color in enumerate(active_colors):
            # Sort values numerically
            sorted_values = sorted(discard_dict[color])
            display_color = translate_color(color, self.is_german)
            discard_text = (
                f"{display_color}: " + ", ".join(map(str, sorted_values))
                if sorted_values
                else f"{display_color}: "
            )

            # Render text
            text_surface = self.small_font.render(discard_text, True, BLACK)
            text_x = LOG_BOX_X + 10
            text_y = LOG_BOX_Y + 10 + i * 30
            self.screen.blit(text_surface, (text_x, text_y))

    # Function to draw storm cards
    def draw_storm_cards(self, lives, total_storm_cards=3):
        storm_label_x = STORM_X + CARD_SPACING
        storm_label_y = STORM_Y
        storm_label = "Gewitterkarten:" if self.is_german else "Storm Cards:"
        label_surface = self.font.render(storm_label, True, BLACK)
        self.screen.blit(label_surface, (storm_label_x, storm_label_y))

        storm_card_x = STORM_X + CARD_SPACING
        storm_card_y = STORM_Y + 2 * CARD_SPACING
        for i in range(total_storm_cards):
            used = i >= lives
            color = BLACK if used else WHITE
            pygame.draw.rect(
                self.screen,
                color,
                (storm_card_x, storm_card_y, CARD_WIDTH, CARD_HEIGHT),
            )
            pygame.draw.rect(
                self.screen,
                BLACK,
                (storm_card_x, storm_card_y, CARD_WIDTH, CARD_HEIGHT),
                2,
            )
            storm_card_x += CARD_WIDTH + CARD_SPACING

    # Function to draw a square or rectangle
    def draw_shape(
        self, x, y, width, height, color, text=None, text_color=None, selected=False
    ):
        if selected:
            pygame.draw.rect(
                self.screen, SELECTED_COLOR, (x - 5, y - 5, width + 10, height + 10)
            )
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        if text:
            text_surface = self.small_font.render(text, True, text_color or BLACK)
            text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
            self.screen.blit(text_surface, text_rect)

    # Draw the fireworks area.
    def draw_fireworks_area(self, fireworks):
        # Label for fireworks
        firework_label_x = FIREWORK_X + 2.5 * CARD_WIDTH + 2 * CARD_SPACING
        firework_label_y = FIREWORK_Y - 30
        fireworks_label = "Feuerwerke" if self.is_german else "Fireworks"
        label_surface = self.font.render(fireworks_label, True, BLACK)
        label_text_rect = label_surface.get_rect(
            center=(firework_label_x, firework_label_y)
        )
        self.screen.blit(label_surface, label_text_rect)

        # Draw each firework stack
        for i, (value, color) in enumerate(fireworks):
            x = FIREWORK_X + i * (CARD_WIDTH + CARD_SPACING)
            self.draw_fireworks(x, FIREWORK_Y, value, color)

    # Function to draw the clue area
    def draw_action_area(
        self,
        other_players,
        selected_card_index,
        selected_clue_index,
        selected_player_index,
        colors,
    ):
        # Row 1: Choose a colour as a hint
        for i, color in enumerate(colors):
            color_spacing = 10 if len(colors) == 6 else 20
            color_x = CLUE_X + i * (SQUARE_SIZE + color_spacing)
            is_selected = selected_clue_index == ("color", i)
            if is_selected:
                pygame.draw.rect(
                    self.screen,
                    SELECTED_COLOR,
                    (color_x - 5, CLUE_Y - 5, SQUARE_SIZE + 10, SQUARE_SIZE + 10),
                )
            self.draw_shape(
                color_x,
                CLUE_Y,
                SQUARE_SIZE,
                SQUARE_SIZE,
                HINTED_CARD_COLORS[color]["bg"],
            )

        # Row 2: Choose a number as a hint
        for i in range(5):
            number_x = CLUE_X + i * (SQUARE_SIZE + CARD_SPACING)
            number_y = CLUE_Y + SQUARE_SIZE + CARD_SPACING
            is_selected = selected_clue_index == ("number", i)
            if is_selected:
                pygame.draw.rect(
                    self.screen,
                    SELECTED_COLOR,
                    (number_x - 5, number_y - 5, SQUARE_SIZE + 10, SQUARE_SIZE + 10),
                )
            self.draw_shape(
                number_x,
                number_y,
                SQUARE_SIZE,
                SQUARE_SIZE,
                "lightgray",
                str(i + 1),
                BLACK,
            )

        # Row 3: Choose a player who gets the hint
        for i, player in enumerate(other_players):
            row = i // 2
            col = i % 2
            player_x = CLUE_X + col * (RECT_WIDTH + CARD_SPACING) + 10
            player_y = CLUE_Y + (2 + row) * (SQUARE_SIZE + CARD_SPACING)
            is_selected = selected_player_index == i
            if is_selected:
                pygame.draw.rect(
                    self.screen,
                    SELECTED_COLOR,
                    (player_x - 5, player_y - 5, RECT_WIDTH + 10, RECT_HEIGHT + 10),
                )
            self.draw_shape(
                player_x, player_y, RECT_WIDTH, RECT_HEIGHT, "lightgray", player, BLACK
            )

        # action buttoms
        buttom_y = CLUE_Y + (3 + (len(other_players) - 1) // 2) * (
            SQUARE_SIZE + CARD_SPACING
        )
        give_hint_label = "Hinweis geben" if self.is_german else "Give Hint"
        play_card_label = "Karte spielen" if self.is_german else "Play Card"
        discard_label = "Abwerfen" if self.is_german else "Discard"

        # give clue buttom
        if selected_clue_index and selected_player_index is not None:
            self.draw_shape(
                CLUE_X + CARD_SPACING,
                buttom_y,
                2 * RECT_WIDTH,
                RECT_HEIGHT,
                (30, 144, 255),
                give_hint_label,
                WHITE,
            )
        else:
            self.draw_shape(
                CLUE_X + CARD_SPACING,
                buttom_y,
                2 * RECT_WIDTH,
                RECT_HEIGHT,
                GRAY,
                give_hint_label,
                BLACK,
            )

        # play card buttom
        if selected_card_index is not None:
            self.draw_shape(
                CLUE_X + CARD_SPACING,
                buttom_y + RECT_HEIGHT + CARD_SPACING,
                2 * RECT_WIDTH,
                RECT_HEIGHT,
                (50, 200, 50),
                play_card_label,
                WHITE,
            )
        else:
            self.draw_shape(
                CLUE_X + CARD_SPACING,
                buttom_y + RECT_HEIGHT + CARD_SPACING,
                2 * RECT_WIDTH,
                RECT_HEIGHT,
                GRAY,
                play_card_label,
                BLACK,
            )

        # discard buttom
        if selected_card_index is not None:
            self.draw_shape(
                CLUE_X + CARD_SPACING,
                buttom_y + 2 * (RECT_HEIGHT + CARD_SPACING),
                2 * RECT_WIDTH,
                RECT_HEIGHT,
                (200, 50, 50),
                discard_label,
                WHITE,
            )
        else:
            self.draw_shape(
                CLUE_X + CARD_SPACING,
                buttom_y + 2 * (RECT_HEIGHT + CARD_SPACING),
                2 * RECT_WIDTH,
                RECT_HEIGHT,
                GRAY,
                discard_label,
                BLACK,
            )

        # Draw a border
        pygame.draw.rect(
            self.screen,
            BLACK,
            (
                CLUE_X - CARD_SPACING,
                CLUE_Y - CARD_SPACING,
                5 * SQUARE_SIZE + 6 * CARD_SPACING,
                buttom_y + 3 * (RECT_HEIGHT + CARD_SPACING),
            ),
            3,
        )

    # Draw the game over popup
    def draw_game_over_popup(self, score, is_host):
        # Semi-transparent background
        popup_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        popup_surface.fill((0, 0, 0, 180))  # Semi-transparent black
        self.screen.blit(popup_surface, (0, 0))

        # Dialog box
        popup_rect = pygame.Rect(400, 200, 400, 300)
        pygame.draw.rect(self.screen, (255, 255, 255), popup_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), popup_rect, 5)  # Border

        # Display text
        if score <= 5:
            result = [
                "Oje!" if self.is_german else "Oh no!",
                "Die Zuschauer buhen." if self.is_german else "The audience boos.",
            ]
        elif 5 < score <= 10:
            result = [
                "Schwach!" if self.is_german else "Weak!",
                "Kaum Applaus." if self.is_german else "Hardly any applause.",
            ]
        elif 10 < score <= 15:
            result = [
                "OK!" if self.is_german else "OK!",
                "Die Zuschauer sind Besseres gewohnt."
                if self.is_german
                else "The audience is used to better.",
            ]
        elif 15 < score <= 20:
            result = [
                "Gut!" if self.is_german else "Good!",
                "Die Zuschauer sind erfreut."
                if self.is_german
                else "The audience is pleased.",
            ]
        elif 20 < score <= 24:
            result = [
                "Sehr gut!" if self.is_german else "Very good!",
                "Die Zuschauer sind begeistert."
                if self.is_german
                else "The audience is excited.",
            ]
        elif score == 25:
            result = [
                "Legendär!" if self.is_german else "Legendary!",
                "Die Zuschauer werden diese Show nie vergessen."
                if self.is_german
                else "The audience will never forget this show.",
            ]

        title_text = self.number_font.render(
            "Spielende" if self.is_german else "Game Over", True, BLACK
        )
        score_text = self.font.render(
            f"Punkte: {score}" if self.is_german else f"Score: {score}", True, BLACK
        )

        title_text_rect = title_text.get_rect(
            center=(popup_rect.centerx, popup_rect.top + 40)
        )
        score_text_rect = score_text.get_rect(
            center=(popup_rect.centerx, popup_rect.top + 100)
        )
        for i, line in enumerate(result):
            result_text = self.font.render(line, True, BLACK)
            self.screen.blit(result_text, (420, 320 + i * 40))
        self.screen.blit(title_text, title_text_rect)
        self.screen.blit(score_text, score_text_rect)

        # Close button
        close_label = "SCHLIEßEN" if self.is_german else "CLOSE"
        restart_label = "NEUSTART" if self.is_german else "RESTART"
        self.draw_shape(450, 420, 120, 50, (200, 50, 50), close_label, WHITE)
        if is_host:
            self.draw_shape(650, 420, 120, 50, (255, 255, 0), restart_label, BLACK)
        else:
            self.draw_shape(650, 420, 120, 50, "lightgray", restart_label, BLACK)
