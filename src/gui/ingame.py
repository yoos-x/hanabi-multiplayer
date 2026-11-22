import pygame
import logging

from gui.renderer import Renderer

# Global Constants
## screen dimensions
WIDTH, HEIGHT = 1200, 800

##colors
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

## Card settings
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


class GamingPage:
    def __init__(self, game_logic, client):
        self.client = client
        self.client.set_callback("game_update", self.on_game_update)
        self.game_state = None
        self.logger = logging.getLogger(__name__)
        self.is_german = self.client.is_german

        self.font = pygame.font.SysFont("Arial", 24)
        self.number_font = pygame.font.SysFont("arialblack", 32)
        self.small_font = pygame.font.SysFont("Arial", 22)

        self.screen = pygame.display.get_surface()

        self.renderer = Renderer(self.screen, self.client)
        self.game = game_logic
        self.colors = self.game.colors

        self.username = self.game.username
        self.players_list = self.game.players_list
        self.host = self.game.host
        self.is_host = self.username == self.host
        self.hinted_cards = {
            player: [{} for _ in range(5)] for player in self.players_list
        }
        self.other_players = [p for p in self.players_list if p != self.username]

        # Static variables
        self.max_score = self.game.max_score
        self.max_clue_number = self.game.max_clue_number
        self.total_storm_cards = self.game.total_storm_cards

        # Dynamic variables
        self.hands = []
        self.fireworks = []
        self.logs = []
        self.discard_pile = []

        self.current_turn = self.players_list.index(self.host)
        self.turn_number = 0
        self.score = 0
        self.clue_number = self.max_clue_number
        self.remaining_cards = 0
        self.storm_cards_number = self.total_storm_cards
        # Selection states
        self.selected_card_index = None
        self.selected_clue_index = None
        self.selected_player_index = None
        self.showing_logs = True

        # Initialize game state
        self.get_current_state()

    def on_game_update(self):
        self.logger.info("Game update received, updating UI...")
        # Fetch the latest game state
        self.game_state = self.client.game_logic.get_game_state()
        self.get_current_state()
        pygame.display.update()
        self.logger.info("UI successfully updated after game_update.")

    # Get the current state from GameLogic
    def get_current_state(self):
        game_state = self.game.get_current_state()

        self.hands = game_state["hands"]
        self.hinted_cards = game_state["hinted_cards"]
        self.fireworks = [
            (value, color) for color, value in game_state["fireworks"].items()
        ]
        self.logs = game_state["logs"]
        self.current_turn = game_state["current_turn"]
        self.turn_number = game_state["turn_number"]
        self.score = game_state["score"]
        self.clue_number = game_state["clue_number"]
        self.remaining_cards = game_state["deck_size"]
        self.storm_cards_number = game_state["storm_cards_number"]
        self.discard_pile = game_state["discard_pile"]
        self.game_over = game_state["game_over"]

    # change current turn
    def next_turn(self):
        self.logger.info("Next turn triggered, updating game state.")

        # Boardcasting the new game state status to others
        if self.client.username == self.game.players_list[self.game.current_turn]:
            self.game.next_turn()
            new_game_state = self.game.get_game_state()
            self.client.send_message(
                "game_update",
                room_name=self.client.current_room["room_name"],
                game_state=new_game_state,
            )

        # reset selection
        self.selected_card_index = None
        self.selected_clue_index = None
        self.selected_player_index = None

        # Update state
        self.get_current_state()

    # Draw player's area including their name and cards
    def draw_player_area(self, player, index):
        # Highlight current player
        if index == self.current_turn:
            arrow_x = NAME_WIDTH + len(self.hands[0]) * (CARD_WIDTH + CARD_SPACING) + 10
            pygame.draw.rect(
                self.screen,
                (200, 255, 200),
                (
                    0,
                    PLAYER_SPACING * index + 10,
                    arrow_x + 2 * CARD_SPACING,
                    PLAYER_SPACING,
                ),
            )
            arrow_surface = self.number_font.render("←", True, BLACK)
            self.screen.blit(arrow_surface, (arrow_x, PLAYER_SPACING * index + 40))

        # Draw player name
        name_surface = self.font.render(player, True, BLACK)
        name_x = 10
        name_y = PLAYER_SPACING * index + 50
        self.screen.blit(name_surface, (name_x, name_y))

        # Draw player's hand
        for j, (value, color) in enumerate(self.hands[index]):
            card_x = NAME_WIDTH + CARD_SPACING + j * (CARD_WIDTH + CARD_SPACING)
            card_y = PLAYER_SPACING * index + 20
            hinted = self.hinted_cards[player][j]
            self.renderer.draw_card(
                card_x,
                card_y,
                value,
                color,
                hide_value=(player == self.username),
                selected=(index == self.current_turn and j == self.selected_card_index),
                hinted=hinted,
            )

    # Function to draw info box
    def draw_game_info_box(self):
        # Game infos
        round_label = "Runde" if self.is_german else "Round"
        score_label = "Punktezahl" if self.is_german else "Score"
        hints_label = "Hinweise" if self.is_german else "Hints"
        remaining_cards_label = "übrige Karten" if self.is_german else "Remaining Cards"
        no_hints_text = (
            "Es gibt keine Hinweise mehr!" if self.is_german else "No hints left!"
        )

        info_lines = [
            f"{round_label}: {self.turn_number}",
            f"{score_label}: {self.score}/{self.max_score}",
            f"{hints_label}: {self.clue_number}",
            f"{remaining_cards_label}: {self.remaining_cards}",
        ]
        if self.clue_number == 0:
            info_lines.append(no_hints_text)
        for i, line in enumerate(info_lines):
            text_surface = self.small_font.render(line, True, BLACK)
            text_x = INFO_BOX_X + CARD_SPACING
            text_y = INFO_BOX_Y + RECT_HEIGHT + 2 * CARD_SPACING + i * 40
            self.screen.blit(text_surface, (text_x, text_y))

        # Buttons
        exit_text = "Beenden" if self.is_german else "Exit"
        save_text = "Speichern" if self.is_german else "Save"

        self.renderer.draw_shape(
            INFO_BOX_X + CARD_SPACING,
            INFO_BOX_Y + CARD_SPACING,
            RECT_WIDTH,
            RECT_HEIGHT,
            (200, 50, 50),
            exit_text,
            WHITE,
        )
        if self.host == self.username:
            save_color = (255, 255, 0)
        else:
            save_color = GRAY
        self.renderer.draw_shape(
            INFO_BOX_X + RECT_WIDTH + 2 * CARD_SPACING,
            INFO_BOX_Y + CARD_SPACING,
            RECT_WIDTH,
            RECT_HEIGHT,
            save_color,
            save_text,
            BLACK,
        )

    # Save the game state
    def save_game(self):
        file_path = "saved_game.json"
        self.game.save_game(file_path)

    def render(self):
        try:
            # Clear screen
            self.screen.fill((255, 255, 255))  # White background

            # Draw the players and their hands
            for i, player in enumerate(self.players_list):
                self.draw_player_area(player, i)

            # Draw the fireworks area
            self.renderer.draw_fireworks_area(self.fireworks)

            # Draw the storm cards
            self.renderer.draw_storm_cards(
                self.storm_cards_number, self.total_storm_cards
            )

            # Draw the action area
            if self.players_list[self.current_turn] == self.username:
                self.renderer.draw_action_area(
                    self.other_players,
                    self.selected_card_index,
                    self.selected_clue_index,
                    self.selected_player_index,
                    self.colors,
                )

            # Draw the game information
            self.draw_game_info_box()

            # Draw the action logs or discard pile
            self.renderer.draw_log_discard_buttons()
            if self.showing_logs:
                self.renderer.draw_log_box(self.logs)
            else:
                self.renderer.draw_discard_pile(self.discard_pile, self.fireworks)

            if self.game.game_over:
                self.renderer.draw_game_over_popup(self.score, self.is_host)

        except Exception as e:
            self.logger.error(f"Render error: {str(e)}")
            import traceback

            logging.error("An exception occurred:\n%s", traceback.format_exc())

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quit"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos

            # Define the exit and save button areas
            exit_button_rect = pygame.Rect(
                INFO_BOX_X + CARD_SPACING,
                INFO_BOX_Y + CARD_SPACING,
                RECT_WIDTH,
                RECT_HEIGHT,
            )
            save_button_rect = pygame.Rect(
                INFO_BOX_X + RECT_WIDTH + 2 * CARD_SPACING,
                INFO_BOX_Y + CARD_SPACING,
                RECT_WIDTH,
                RECT_HEIGHT,
            )

            # Handle exit button click
            if exit_button_rect.collidepoint(event.pos):
                self.client.exit_game()
                if self.client.current_room:
                    self.client.leave_game(self.client.current_room["room_name"])
                    self.client.send_message("get_lobby_update")
                    pygame.time.delay(100)
                    self.client._trigger_callback("lobby_update")
                return "exit"

            # Handle save button click
            elif save_button_rect.collidepoint(event.pos):
                self.game.save_game("saved_game.json")
                self.client.send_message("get_lobby_update")
                return None

            # Click log button
            log_button_rect = pygame.Rect(881, LOG_BOX_Y - 29, 150, 30)
            if log_button_rect.collidepoint(event.pos):
                self.showing_logs = True
                return None

            # Click discardpile button
            discard_pile_rect = pygame.Rect(1030, LOG_BOX_Y - 29, 150, 30)
            if discard_pile_rect.collidepoint(event.pos):
                self.showing_logs = False
                return None

            # When game over
            if self.game.game_over:
                close_button = pygame.Rect(450, 420, 100, 50)
                restart_button = pygame.Rect(650, 420, 100, 50)
                if close_button.collidepoint(event.pos):
                    self.logger.info("Close button clicked!")
                    self.client.exit_game()
                    if self.client.current_room:
                        self.client.leave_game(self.client.current_room["room_name"])
                        self.client.send_message("get_lobby_update")
                        pygame.time.delay(100)
                        self.client._trigger_callback("lobby_update")
                    return "exit"
                elif restart_button.collidepoint(event.pos):
                    if self.username == self.host:
                        self.logger.info("Restart button clicked!")
                        self.game.handle_game_reset()
                        self.game.game_over = False
                        self.get_current_state()
                    else:
                        self.logger.warning("Only host can restart the game.")
                    return None

            # Click the clue area
            # Choose a color
            for i, color in enumerate(self.colors):
                color_spacing = 10 if len(self.colors) == 6 else 20
                rect_x = CLUE_X + i * (SQUARE_SIZE + color_spacing)
                rect_y = CLUE_Y
                if (
                    rect_x <= mouse_x <= rect_x + SQUARE_SIZE
                    and rect_y <= mouse_y <= rect_y + SQUARE_SIZE
                ):
                    if self.selected_clue_index == ("color", i):
                        self.selected_clue_index = None
                    else:
                        self.selected_clue_index = ("color", i)
            # Choose a number
            for i in range(5):
                rect_x = CLUE_X + i * (SQUARE_SIZE + CARD_SPACING)
                rect_y = CLUE_Y + SQUARE_SIZE + CARD_SPACING
                if (
                    rect_x <= mouse_x <= rect_x + SQUARE_SIZE
                    and rect_y <= mouse_y <= rect_y + SQUARE_SIZE
                ):
                    if self.selected_clue_index == ("number", i):
                        self.selected_clue_index = None
                    else:
                        self.selected_clue_index = ("number", i)
            # Choose a player
            for i, player in enumerate(self.other_players):
                row = i // 2
                col = i % 2
                rect_x = CLUE_X + col * (RECT_WIDTH + CARD_SPACING)
                rect_y = CLUE_Y + (2 + row) * (SQUARE_SIZE + CARD_SPACING)
                if (
                    rect_x <= mouse_x <= rect_x + RECT_WIDTH
                    and rect_y <= mouse_y <= rect_y + RECT_HEIGHT
                ):
                    if self.selected_player_index == i:
                        self.selected_player_index = None
                    else:
                        self.selected_player_index = i

            # Click on the player's own card
            if self.players_list[self.current_turn] == self.username:
                for j, (value, color) in enumerate(self.hands[self.current_turn]):
                    card_x = NAME_WIDTH + CARD_SPACING + j * (CARD_WIDTH + CARD_SPACING)
                    card_y = PLAYER_SPACING * self.current_turn + 20
                    if (
                        card_x <= mouse_x <= card_x + CARD_WIDTH
                        and card_y <= mouse_y <= card_y + CARD_HEIGHT
                    ):
                        if self.selected_card_index == j:
                            self.selected_card_index = None
                        else:
                            self.selected_card_index = j

            # Click the action buttons
            # Give Clue
            action_x = CLUE_X + CARD_SPACING
            action_y = (
                CLUE_Y
                + (3 + (len(self.other_players) - 1) // 2)
                * (SQUARE_SIZE + CARD_SPACING)
                + CARD_SPACING
            )
            if (
                action_x <= mouse_x <= action_x + 2 * RECT_WIDTH
                and action_y - RECT_HEIGHT // 2
                <= mouse_y
                <= action_y + RECT_HEIGHT * 1.5
            ):
                if self.game.game_over:
                    self.logger.warning("Game is over. No more actions allowed.")
                    return None
                if self.selected_clue_index and self.selected_player_index is not None:
                    clue_type, clue_value = self.selected_clue_index
                    target_player = self.other_players[self.selected_player_index]
                    success = self.game.give_hint(
                        self.username, target_player, clue_type, clue_value
                    )
                    if success:
                        if clue_type == "color":
                            c = self.fireworks[clue_value][1]
                            for i, card in enumerate(
                                self.hands[self.players_list.index(target_player)]
                            ):
                                if card[1] == c:
                                    self.hinted_cards[target_player][i]["color"] = c
                            self.logger.info(
                                f"Clue given: {clue_type} {c} to {target_player}"
                            )
                        elif clue_type == "number":
                            n = clue_value + 1
                            for i, card in enumerate(
                                self.hands[self.players_list.index(target_player)]
                            ):
                                if card[0] == n:
                                    self.hinted_cards[target_player][i]["number"] = n
                            self.logger.info(
                                f"Clue given: {clue_type} {n} to {target_player}"
                            )
                    else:
                        self.logger.info("Unable to give a clue.")
                    self.next_turn()

            # Play Card
            if (
                action_x <= mouse_x <= action_x + 2 * RECT_WIDTH
                and action_y + RECT_HEIGHT + CARD_SPACING
                <= mouse_y
                <= action_y + RECT_HEIGHT + CARD_SPACING + RECT_HEIGHT * 1.5
            ):
                if self.game.game_over:
                    self.logger.warning("Game is over. No more actions allowed.")
                    return None
                if self.selected_card_index is not None:
                    result = self.game.play_card(
                        self.current_turn, self.selected_card_index
                    )
                    if result == "success":
                        self.logger.info("Card played successfully!")
                    elif result == "failure":
                        self.logger.info("Failed to play card, storm card used!")
                    elif result == "game_over":
                        self.logger.info("Game Over! All storm cards used.")
                    elif result == "invalid":
                        self.logger.warning(
                            "Invalid action: Cannot play the selected card."
                        )
                    self.next_turn()

            # Discard
            if (
                action_x <= mouse_x <= action_x + 2 * RECT_WIDTH
                and action_y + 2 * (RECT_HEIGHT + CARD_SPACING)
                <= mouse_y
                <= action_y + 2 * (RECT_HEIGHT + CARD_SPACING) + RECT_HEIGHT * 1.5
            ):
                if self.game.game_over:
                    self.logger.warning("Game is over. No more actions allowed.")
                    return None
                if self.selected_card_index is not None:
                    success = self.game.discard_card(
                        self.current_turn, self.selected_card_index
                    )
                    if success:
                        self.logger.info("Card discarded successfully!")
                    else:
                        self.logger.info("Failed to discard card.")
                    self.next_turn()

        # mouse wheel to scroll from second code
        elif event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            log_box_rect = pygame.Rect(
                LOG_BOX_X, LOG_BOX_Y, LOG_BOX_WIDTH, LOG_BOX_HEIGHT
            )

            # Only scroll if mouse is over log box
            if log_box_rect.collidepoint(mouse_x, mouse_y):
                self.renderer.scroll_offset -= event.y
                self.renderer.scroll_offset = max(
                    0, min(self.renderer.scroll_offset, self.renderer.max_scroll)
                )

        return None
