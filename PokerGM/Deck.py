import random

class Deck:
    def __init__(self):
        self.cards = []
        self.build()
        self.shuffle()

    def build(self):
        self.cards = []
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['h', 'd', 'c', 's'] # h=hearts, d=diamonds, c=clubs, s=spades
        for suit in suits:
            for rank in ranks:
                self.cards.append(rank + suit) # e.g., "Ah", "Td", "7s"

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        else:
            return None # No cards left

    def burn_card(self):
        if len(self.cards) > 0:
            self.cards.pop() # Remove top card without returning it

    def reset_and_shuffle(self):
        self.build()
        self.shuffle()

    def __len__(self):
        return len(self.cards)