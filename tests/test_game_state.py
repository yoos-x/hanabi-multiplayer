import pytest
import json
import copy
import logging
from src.game.game_state import GameLogic


@pytest.fixture
def game_state():
    players = ["Emma", "Hanna", "Yuxin", "Kailai"]
    username = "Yuxin"
    host = "Yuxin"
    variant = "Multicolor"

    return GameLogic(players, username, host, variant)


# test for the methode create a deck


def test_create_deck(game_state):
    if game_state.variant in ["Farbrausch", "Multicolor"]:
        expected_deck_size = 60
    else:
        expected_deck_size = 50
    deck = game_state.create_deck()
    assert len(deck) == expected_deck_size
    card_counts = {
        (number, color): deck.count((number, color))
        for number in game_state.numbers
        for color in game_state.colors
    }

    for number, count in game_state.card_distribution.items():
        for color in game_state.colors:
            assert card_counts[(number, color)] == count


# test for the methode deal initial hands


def test_deal_initial_hands(game_state):
    number_players = len(game_state.players_list)
    initial_deck_size = len(game_state.deck)

    expected_hand_size = 5 if number_players <= 3 else 4
    hands = game_state.deal_initial_hands()
    assert all(len(hand) == expected_hand_size for hand in hands)

    expected_deck_size = initial_deck_size - (number_players * expected_hand_size)
    assert len(game_state.deck) == expected_deck_size

    all_cards = [card for hand in hands for card in hand]

    # all cards should be have vaild colors and numbers
    assert all(
        card[0] in game_state.numbers and card[1] in game_state.colors
        for card in all_cards
    )


# test the method save game


def test_save_game(game_state, tmp_path):
    # creating temporary data
    file_path = tmp_path / "saved_game.json"

    # saving the play state
    game_state.save_game(file_path)

    initial_game_state = {
        "username": game_state.username,
        "host": game_state.host,
        "max_score": game_state.max_score,
        "max_clue_number": game_state.max_clue_number,
        "total_storm_cards": game_state.total_storm_cards,
        "hands": game_state.hands,
        "fireworks": game_state.fireworks,
        "logs": game_state.logs,
        "current_turn": game_state.current_turn,
        "turn_number": game_state.turn_number,
        "score": game_state.score,
        "clue_number": game_state.clue_number,
        "deck_size": game_state.deck_size,
        "storm_cards_number": game_state.storm_cards_number,
    }

    with open(file_path, "r") as f:  # r for reading access
        saved_game_state = json.load(f)

    # Converting hands from lists to tuples
    saved_game_state["hands"] = [
        [tuple(card) for card in player_hand]
        for player_hand in saved_game_state["hands"]
    ]
    assert saved_game_state == initial_game_state


# test the method load game


def test_load_game(game_state, tmp_path):
    file_path = tmp_path / "saved_game.json"
    game_settings = {
        "username": game_state.username,
        "players_list": game_state.players_list,
        "host": game_state.host,
        "max_score": game_state.max_score,
        "max_clue_number": game_state.max_clue_number,
        "total_storm_cards": game_state.total_storm_cards,
        "hands": game_state.hands,
        "fireworks": game_state.fireworks,
        "logs": game_state.logs,
        "current_turn": game_state.current_turn,
        "turn_number": game_state.turn_number,
        "score": game_state.score,
        "clue_number": game_state.clue_number,
        "deck_size": game_state.deck_size,
        "storm_cards_number": game_state.storm_cards_number,
    }
    with open(file_path, "w") as f:
        json.dump(game_settings, f)

    assert game_state.username == game_settings["username"]
    assert game_state.players_list == game_settings["players_list"]
    assert game_state.host == game_settings["host"]
    assert game_state.max_score == game_settings["max_score"]
    assert game_state.max_clue_number == game_settings["max_clue_number"]
    assert game_state.total_storm_cards == game_settings["total_storm_cards"]
    assert game_state.hands == game_settings["hands"]
    assert game_state.fireworks == game_settings["fireworks"]
    assert game_state.logs == game_settings["logs"]
    assert game_state.current_turn == game_settings["current_turn"]
    assert game_state.turn_number == game_settings["turn_number"]
    assert game_state.score == game_settings["score"]
    assert game_state.clue_number == game_settings["clue_number"]
    assert game_state.deck_size == game_settings["deck_size"]
    assert game_state.storm_cards_number == game_settings["storm_cards_number"]


# test for playing a card


def test_play_card(game_state):
    # diffrent scenarios

    game_state.hands = [[(1, "Green"), (2, "Blue"), (4, "Red")]]
    game_state.fireworks = {"Green": 0, "Blue": 1, "Red": 0, "Yellow": 0, "Purple": 0}
    game_state.deck = [(4, "Yellow"), (5, "Red")]
    game_state.score = 0
    game_state.storm_cards_number = 3

    # scenario 1: successful move
    result = game_state.play_card(current_turn=0, selected_card_index=1)
    assert result == "success"
    assert game_state.score == 1
    game_state.fireworks["Blue"] = 2
    assert game_state.fireworks["Blue"] == 2
    assert len(game_state.hands[0]) == 3
    new_card = game_state.deck.pop()
    game_state.hands[0].append(new_card)
    assert game_state.hands[0][-1] == (4, "Yellow")  # a new card was drawn

    # scenario 2: invaild card_index
    result = game_state.play_card(current_turn=0, selected_card_index=5)
    assert result == "invalid"
    assert "Ungültige Aktion" in game_state.logs[-1]

    #  scenario 3: play move failed
    result = game_state.play_card(current_turn=0, selected_card_index=2)
    assert result == "failure"
    assert game_state.storm_cards_number == 2
    assert len(game_state.discard_pile) > 0
    assert "schlägt fehl eine" in game_state.logs[-1]

    # scenario 4: game over: no lives left!
    game_state.storm_cards_number = 1
    result = game_state.play_card(current_turn=0, selected_card_index=2)
    assert game_state.storm_cards_number == 0
    assert result == "game_over"
    assert game_state.game_over is True
    assert "Spiel vorbei - Keine Leben mehr übrig" in game_state.logs[-1]

    # scenario 5: winning the game
    game_state.hands = [[(5, "Green"), (2, "Blue"), (1, "Red")]]
    game_state.fireworks = {"Green": 4, "Blue": 4, "Red": 4, "Yellow": 4, "Purple": 4}
    game_state.score = 24
    game_state.max_score = 25
    game_state.game_over = False

    result = game_state.play_card(current_turn=0, selected_card_index=0)
    assert result == "success"
    assert game_state.game_over is True
    assert "Ihr gewinnt das Spiel!" in game_state.logs[-1]


# test for the methode dischard a card


def test_discard_card(game_state):
    player_index = 0
    card_index = 0

    # controll if the player and the hand is corectly initialize
    assert 0 <= player_index < len(game_state.hands)
    assert len(game_state.hands[player_index]) > card_index

    # save the initial conditions
    initial_hand = copy.deepcopy(game_state.hands[player_index])
    initial_clue_number = game_state.clue_number
    # [:] sytntax for every element in array
    initial_deck_size = game_state.deck_size
    initial_dischard_pile = game_state.discard_pile[:]
    initial_logs = game_state.logs[:]

    # check the success
    result = game_state.discard_card(player_index, card_index)
    discard_card = initial_hand[card_index]
    assert result is True

    # check if the card is removed and correctly placed on the discard_pile

    assert discard_card in game_state.discard_pile
    assert game_state.discard_pile[-1] == discard_card

    # check if a new card is drawn
    if initial_deck_size > 0:
        assert len(game_state.hands[player_index]) == len(initial_hand)
    else:
        assert len(game_state.hands[player_index]) == len(initial_hand) - 1

    # check if the clue_number is correctly restored
    if initial_clue_number < 8:
        assert game_state.clue_number == initial_clue_number + 1
    else:
        assert game_state.clue_number == initial_clue_number

    # check if the actions are correct in the protocol
    expected_action = f"{game_state.players_list[player_index]} wirft {
        discard_card[1]
    } {discard_card[0]} ab"
    assert game_state.logs[-1] == expected_action
    assert len(game_state.logs) == len(initial_logs) + 1

    # Check if the inputs are valid
    invalid_card_index = len(game_state.hands[player_index])  # invalid card_index

    if invalid_card_index < len(game_state.hands[player_index]):
        invalid_result = game_state.hands[player_index][invalid_card_index]
        assert invalid_result is False


# test for the methode give a hint


def test_give_hint(game_state):
    # testing of diffrent scenarios
    game_state.clue_number = 3
    game_state.active_player = "Yuxin"
    game_state.players_list = ["Yuxin", "Hanna", "Kailai", "Emma"]
    game_state.hands = [
        [(1, "Red"), (2, "Blue"), (3, "Green")],  # hand from Yuxin
        [(2, "Red"), (3, "Red"), (4, "Blue")],  # hand from Hanna
        [(1, "Yellow"), (2, "Yellow"), (3, "Yellow")],  # hand from Kailai
        [(3, "Purple"), (1, "Purple"), (2, "Green")],  # hand from Emma
    ]
    game_state.colors = {
        "Red": "Red",
        "Blue": "Blue",
        "Green": "Green",
        "Yellow": "Yellow",
        "Purple": "Purple",
    }
    game_state.logs = []

    # scenario 1: vaild hint: success
    result = game_state.give_hint("Yuxin", "Hanna", "color", "Red")
    assert result is True
    assert game_state.clue_number == 2
    assert (
        game_state.logs[-1]
        == "Yuxin gibt Hanna den Hinweis über die Karten mit der color Red, es passen 2 Karte(n)."
    )

    # scenario 2: vailid hint: failure
    result = game_state.give_hint("Kailai", "Emma", "color", "Yellow")
    assert result is True
    assert game_state.clue_number == 1
    assert (
        game_state.logs[-1]
        == "Kailai gibt Emma den Hinweis über die Karten mit der color Yellow, aber es wurden keine passenden Karten gefunden."
    )

    # Szenario 3: hint on own hand: invaild
    result = game_state.give_hint("Yuxin", "Yuxin", "color", "Red")
    assert result is False
    assert game_state.clue_number == 1  # clue_number stays the same

    # scenario 4: hint by missing clue: invaild
    game_state.clue_number = 0
    result = game_state.give_hint("Yuxin", "Hanna", "number", 2)
    assert result is False
    assert game_state.clue_number == 0  # clue_number stays the same

    # scenario 5: hint at number: success
    game_state.clue_number = 1
    result = game_state.give_hint("Yuxin", "Kailai", "number", 2)
    assert result is True
    assert game_state.clue_number == 0
    assert (
        game_state.logs[-1]
        == "Yuxin gibt Kailai den Hinweis über die Karten mit der number 3, es passen 1 Karte(n)."
    )


# test for the methode of getting the current state


def test_get_current_state(game_state):
    expected_state = {
        "hands": game_state.hands,
        "fireworks": game_state.fireworks,
        "logs": game_state.logs,
        "current_turn": game_state.current_turn,
        "turn_number": game_state.turn_number,
        "score": game_state.score,
        "clue_number": game_state.clue_number,
        "deck_size": game_state.deck_size,
        "storm_cards_number": game_state.storm_cards_number,
        "hinted_cards": game_state.hinted_cards,
        "discard_pile": game_state.discard_pile,
        "game_over": game_state.game_over,
    }
    actual_state = game_state.get_current_state()
    assert actual_state == expected_state


# test for the method set the state of the game


def test_set_state(game_state):
    new_state = {
        "hands": [(1, "Green"), (2, "Blue"), (4, "Red")],
        "fireworks": {"Green": 2, "Blue": 1, "Red": 1, "Yellow": 3, "Purple": 0},
        "logs": ["Emma played a card.", "Yuxin discarded a card."],
        "current_turn": "Alice",
        "turn_number": 5,
        "score": 8,
        "clue_number": 2,
        "deck_size": 40,
        "storm_cards_number": 1,
    }
    game_state.set_state(new_state)

    assert game_state.hands == new_state["hands"]
    assert game_state.fireworks == new_state["fireworks"]
    assert game_state.logs == new_state["logs"]
    assert game_state.current_turn == new_state["current_turn"]
    assert game_state.turn_number == new_state["turn_number"]
    assert game_state.score == new_state["score"]
    assert game_state.clue_number == new_state["clue_number"]
    assert game_state.deck_size == new_state["deck_size"]
    assert game_state.storm_cards_number == new_state["storm_cards_number"]


# test the method update state


def test_update_state(game_state, caplog):
    # simulated datas
    new_state = {
        "players": [
            {"name": "Yuxin", "hand": [(1, "Green"), (2, "Blue"), (4, "Red")]},
            {"name": "Emma", "hand": [(3, "Green"), (4, "Yellow"), (5, "Blue")]},
        ],
        "hinted_cards": {"Yuxin": [{}, {}, {}], "Emma": [{}, {}, {}]},
        "fireworks": {"Green": 0, "Blue": 1, "Purple": 0, "Yellow": 3, "Red": 3},
        "clue_number": 3,
        "current_turn": 1,
        "storm_cards_number": 2,
        "game_over": True,
        "score": 6,
        "turn_number": 4,
        "logs": ["Emma played a card.", "Yuxin discarded a card."],
        "discard_pile": [(2, "Blue"), (1, "Red")],
    }

    game_state.update_state(new_state)

    # check, if the datas are correcttly put
    assert game_state.hands == [
        [(1, "Green"), (2, "Blue"), (4, "Red")],
        [(3, "Green"), (4, "Yellow"), (5, "Blue")],
    ]
    assert game_state.fireworks == {
        "Green": 0,
        "Blue": 1,
        "Purple": 0,
        "Yellow": 3,
        "Red": 3,
    }
    assert game_state.clue_number == new_state["clue_number"]
    assert game_state.storm_cards_number == new_state["storm_cards_number"]
    assert game_state.score == new_state["score"]
    assert game_state.turn_number == new_state["turn_number"]
    assert game_state.logs == new_state["logs"]
    assert game_state.discard_pile == new_state["discard_pile"]
    assert game_state.current_turn == new_state["current_turn"]
    assert game_state.game_over == new_state["game_over"]
    # check if logging works for the error
    with caplog.at_level(logging.ERROR):
        game_state.update_state({"logs": ["new game"]})

    assert "Missing 'players' field in game state update!" in caplog.text


# test the method get game state


def test_get_game_state(game_state):
    expected_player_actions = {
        "players": [
            {"name": player, "hand": game_state.hands[i]}
            for i, player in enumerate(game_state.players_list)
        ],
        "hands": game_state.hands,
        "hinted_cards": game_state.hinted_cards,
        "fireworks": game_state.fireworks,
        "logs": game_state.logs,
        "current_turn": game_state.current_turn,
        "turn_number": game_state.turn_number,
        "score": game_state.score,
        "clue_number": game_state.clue_number,
        "deck_size": game_state.deck_size,
        "storm_cards_number": game_state.storm_cards_number,
        "discard_pile": game_state.discard_pile,
        "game_over": game_state.game_over,
    }
    actual_player_actions = game_state.get_game_state()
    assert actual_player_actions == expected_player_actions


# test for the methode next turn


def test_next_turn(game_state):
    game_state.current_turn = 0
    num_players = len(game_state.players_list)

    # test for all players in the list is circular
    for i in range(3 * num_players):
        expected_turn = (game_state.current_turn + 1) % num_players
        game_state.next_turn()
        assert game_state.current_turn == expected_turn


# testing the methode handle the game reset


def test_handle_game_reset(game_state):
    game_state.game_over = True
    game_state.score = 5
    game_state.clue_number = 3
    game_state.deck = [(1, "Red")]
    game_state.discard_pile = [(2, "Purple"), (3, "Blue")]
    game_state.logs = ["Emma played a card.", "Hanna discarded a card."]
    game_state.storm_cards_number = 1
    game_state.turn_number = 10
    # Call the reset function
    game_state.handle_game_reset()

    # Expected state after the reset
    number_players = len(game_state.players_list)
    expected_hand_size = 5 if number_players <= 3 else 4
    total_cards_in_deck = (
        60 if game_state.variant in ["Farbrausch", "Multicolor"] else 50
    )
    expected_deck_size = total_cards_in_deck - (
        len(game_state.players_list) * expected_hand_size
    )
    expected_fireworks = {color: 0 for color in game_state.colors}

    assert game_state.game_over is False
    assert game_state.score == 0
    assert game_state.clue_number == game_state.max_clue_number
    assert game_state.storm_cards_number == game_state.total_storm_cards
    assert game_state.turn_number == 1
    assert game_state.logs == []
    assert game_state.discard_pile == []
    assert len(game_state.deck) == expected_deck_size
    assert game_state.fireworks == expected_fireworks
    assert all(len(hand) == expected_hand_size for hand in game_state.hands)
    assert game_state.hinted_cards == {
        player: [{} for _ in range(5)] for player in game_state.players_list
    }

    # check the player-related state
    assert game_state.host == game_state.username
    assert game_state.current_turn == game_state.players_list.index(game_state.host)
    assert game_state.active_player == game_state.current_turn
