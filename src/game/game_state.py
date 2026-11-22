import random
import json
import logging


class GameLogic:
    def __init__(
        self, players, username, host, variant, max_clue_number=8, total_storm_cards=3
    ):
        # Static game settings
        self.colors = ["Red", "Yellow", "Green", "Blue", "Purple"]
        self.variant = variant
        if self.variant == "Farbrausch" or self.variant == "Multicolor":
            self.colors.append("Orange")
        self.numbers = [1, 2, 3, 4, 5]
        self.card_distribution = {1: 3, 2: 2, 3: 2, 4: 2, 5: 1}
        self.total_storm_cards = total_storm_cards
        self.max_score = len(self.colors) * max(self.numbers)
        self.max_clue_number = max_clue_number

        # Player-related information
        self.logger = logging.getLogger(__name__)
        self.players_list = players
        self.username = username
        self.host = host
        self.current_turn = self.players_list.index(host)
        self.active_player = self.current_turn

        # Dynamic game state
        self.game_over = False
        self.deck = self.create_deck()
        self.hands = self.deal_initial_hands()
        self.fireworks = {color: 0 for color in self.colors}
        self.discard_pile = []
        self.logs = []
        self.storm_cards_number = self.total_storm_cards
        self.clue_number = self.max_clue_number
        self.score = 0
        self.hinted_cards = {player: [{} for _ in range(5)] for player in players}

        # State cache
        self.deck_size = len(self.deck)
        self.turn_number = 1

    # Generate and shuffle the deck of cards.
    def create_deck(self):
        deck = []
        for color in self.colors:
            for number, count in self.card_distribution.items():
                deck.extend([(number, color)] * count)
        random.shuffle(deck)
        return deck

    # Distribute initial hands for each player
    def deal_initial_hands(self):
        hands = []
        if len(self.players_list) <= 3:
            hands_number = 5
        elif len(self.players_list) > 3:
            hands_number = 4
        for _ in self.players_list:
            hand = [self.deck.pop() for _ in range(hands_number) if self.deck]
            hands.append(hand)
        return hands

    # Save the current game state to a file
    def save_game(self, file_path="saved_game.json"):
        game_state = {
            "username": self.username,
            "host": self.host,
            "max_score": self.max_score,
            "max_clue_number": self.max_clue_number,
            "total_storm_cards": self.total_storm_cards,
            "hands": self.hands,
            "fireworks": self.fireworks,
            "logs": self.logs,
            "current_turn": self.current_turn,
            "turn_number": self.turn_number,
            "score": self.score,
            "clue_number": self.clue_number,
            "deck_size": self.deck_size,
            "storm_cards_number": self.storm_cards_number,
        }

        with open(file_path, "w") as f:
            json.dump(game_state, f, indent=4)
        self.logger.info(f"Game saved to {file_path}")

    def load_game(self, file_path):
        with open(file_path, "r") as f:
            game_state = json.load(f)

        self.username = game_state["username"]
        self.players_list = game_state["players_list"]
        self.host = game_state["host"]

        self.max_score = game_state["max_score"]
        self.max_clue_number = game_state["max_clue_number"]
        self.total_storm_cards = game_state["total_storm_cards"]

        self.hands = game_state["hands"]
        self.fireworks = game_state["fireworks"]
        self.logs = game_state["logs"]

        self.current_turn = game_state["current_turn"]
        self.turn_number = game_state["turn_number"]
        self.score = game_state["score"]
        self.clue_number = game_state["clue_number"]
        self.deck_size = game_state["deck_size"]
        self.storm_cards_number = game_state["storm_cards_number"]

        self.logger.info(f"Game loaded from {file_path}")

    # Play a card
    def play_card(self, current_turn, selected_card_index):
        if not (0 <= selected_card_index < len(self.hands[current_turn])):
            action = f"Ungültige Aktion: {self.players_list[current_turn]} versucht eine ungültige Karte zu spielen."
            self.logs.append(action)
            return "invalid"

        number, color = self.hands[current_turn][selected_card_index]
        card = number, color
        slot = selected_card_index + 1
        firework_value = self.fireworks[color]

        if number == firework_value + 1:
            self.score += 1
            self.fireworks[color] = number
            action = f'{self.username} spielt erfolgreich eine "{color} {number}" von der Stelle {slot} auf die {color} Feuerwerke!'
            self.logs.append(action)
            if self.score == self.max_score:
                self.game_over = True
                action = "Ihr gewinnt das Spiel!"
                self.logs.append(action)
            else:
                if self.deck:
                    self.hands[current_turn][selected_card_index] = self.deck.pop()
                    self.hinted_cards[self.players_list[current_turn]][
                        selected_card_index
                    ] = {}
            return "success"
        else:
            self.storm_cards_number -= 1
            self.discard_pile.append(card)
            if self.deck:
                self.hands[current_turn][selected_card_index] = self.deck.pop()
                self.hinted_cards[self.players_list[current_turn]][
                    selected_card_index
                ] = {}
            action = f'{self.username} schlägt fehl eine "{color} {number}" von der Stelle {slot} zu spielen...'
            self.logs.append(action)
            if self.storm_cards_number == 0:
                self.game_over = True
                self.logs.append("Spiel vorbei - Keine Leben mehr übrig")
                return "game_over"
            return "failure"

    # Discard
    def discard_card(self, player_index, card_index):
        if not (0 <= card_index < len(self.hands[player_index])):
            return False
        card = self.hands[player_index].pop(card_index)
        self.discard_pile.append(card)

        # draw a new card if avalable
        if self.deck:
            new_card = self.deck.pop()
            self.hands[player_index].insert(card_index, new_card)
            self.hinted_cards[self.players_list[player_index]][card_index] = {}

        # Restore a hint token if not already at maximum
        if self.clue_number < 8:
            self.clue_number += 1

        action = f"{self.players_list[player_index]} wirft {card[1]} {card[0]} ab"
        self.logs.append(action)

        return True

    # Give a hint
    def give_hint(self, from_player, target_player, hint_type, value):
        if self.clue_number <= 0 or target_player == self.active_player:
            return False

        self.clue_number -= 1
        target_hand = self.hands[self.players_list.index(target_player)]
        match_count = 0

        if hint_type == "color":
            value = self.colors[value]
            for _, card_color in target_hand:
                if card_color == value:
                    match_count += 1
        elif hint_type == "number":
            value += 1
            for card_number, _ in target_hand:
                if card_number == value:
                    match_count += 1

        if match_count > 0:
            action = f"{from_player} gibt {target_player} den Hinweis über die Karten mit der {hint_type} {value}, es passen {match_count} Karte(n)."
            self.logs.append(action)
        else:
            action = f"{from_player} gibt {target_player} den Hinweis über die Karten mit der {hint_type} {value}, aber es wurden keine passenden Karten gefunden."
            self.logs.append(action)

        return True

    # Retrieve the current game_state to update the UI.
    def get_current_state(self):
        return {
            "hands": self.hands,
            "fireworks": self.fireworks,
            "logs": self.logs,
            "current_turn": self.current_turn,
            "turn_number": self.turn_number,
            "score": self.score,
            "clue_number": self.clue_number,
            "deck_size": self.deck_size,
            "storm_cards_number": self.storm_cards_number,
            "hinted_cards": self.hinted_cards,
            "discard_pile": self.discard_pile,
            "game_over": self.game_over,
        }

    # set the state
    def set_state(self, state):
        """Set the game state from a dictionary."""
        self.hands = state.get("hands", self.hands)
        self.fireworks = state.get("fireworks", self.fireworks)
        self.logs = state.get("logs", self.logs)
        self.current_turn = state.get("current_turn", self.current_turn)
        self.turn_number = state.get("turn_number", self.turn_number)
        self.score = state.get("score", self.score)
        self.clue_number = state.get("clue_number", self.clue_number)
        self.deck_size = state.get("deck_size", self.deck_size)
        self.storm_cards_number = state.get(
            "storm_cards_number", self.storm_cards_number
        )

    def update_state(self, state):
        """Set the game state from a dictionary."""
        if "players" not in state:
            self.logger.error("Missing 'players' field in game state update!")
            return

        self.logger.info(f"Overwriting game state with: {state}")
        self.players_list = self.players_list
        self.hands = [
            p["hand"] for p in state["players"] if isinstance(p, dict) and "hand" in p
        ]
        self.hinted_cards = state["hinted_cards"]
        self.fireworks = state["fireworks"]
        self.logs = state["logs"]
        self.current_turn = state["current_turn"]
        self.turn_number = state["turn_number"]
        self.score = state["score"]
        self.clue_number = state["clue_number"]
        self.storm_cards_number = state["storm_cards_number"]
        self.discard_pile = state["discard_pile"]
        self.game_over = state["game_over"]
        self.logger.info(f"New game state set: {self.__dict__}")

    # get the actual status of the player action
    def get_game_state(self):
        game_state = {
            "players": [
                {"name": player, "hand": self.hands[i]}
                for i, player in enumerate(self.players_list)
            ],
            "hands": self.hands,
            "hinted_cards": self.hinted_cards,
            "fireworks": self.fireworks,
            "logs": self.logs,
            "current_turn": self.current_turn,
            "turn_number": self.turn_number,
            "score": self.score,
            "clue_number": self.clue_number,
            "deck_size": self.deck_size,
            "storm_cards_number": self.storm_cards_number,
            "discard_pile": self.discard_pile,
            "game_over": self.game_over,
        }

        return game_state

    # Move to the next turn
    def next_turn(self):
        # Update turn information
        self.current_turn = (self.current_turn + 1) % len(self.players_list)
        self.active_player = self.current_turn
        self.turn_number += 1

    # Reset the Game
    def handle_game_reset(self):
        self.game_over = False

        self.host = self.username
        self.current_turn = self.players_list.index(self.host)
        self.active_player = self.current_turn

        self.deck = self.create_deck()
        self.hands = self.deal_initial_hands()
        self.fireworks = {color: 0 for color in self.colors}
        self.discard_pile = []
        self.logs = []

        self.storm_cards_number = self.total_storm_cards
        self.clue_number = self.max_clue_number
        self.score = 0
        self.turn_number = 1
        self.hinted_cards = {
            player: [{} for _ in range(5)] for player in self.players_list
        }
