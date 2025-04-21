class Player:
    def __init__(self, player_list):
        self.players = {name: {"card": [], "pot": 0, "action": None} for name in player_list}

    def set_card(self, player, card):
        self.players[player]["card"].append(card)

    def fold_card(self, player):
        self.players[player]["card"] = []

    def set_pot(self, player, pot):
        self.players[player]["pot"] = pot

    def set_action(self, player, action):
        self.players[player]["action"] = action

    def calculator_player_pot(self, player_name, symbol, number):
        if symbol == '+':
            self.players[player_name]["pot"] += number
        else:
            self.players[player_name]["pot"] = max(0, self.players[player_name]["pot"] - number)

    def get_player_card(self, player_name):
        return self.players[player_name]["card"]

    def get_player_pot(self, player_name):
        return self.players[player_name]["pot"]

    def get_player_action(self, player_name):
        return self.players[player_name]["action"]