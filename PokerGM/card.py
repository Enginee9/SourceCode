class Card:
    def __init__(self, suit=None, rank=None):
        self.suit = suit
        self.rank = rank


class DeckManager:
    def __init__(self):
        self.deck = []

    def create_deck(self):
        suits = ["Clubs", "Diamonds", "Hearts", "Spades"]
        ranks = ["Two", "Three", "Four", "Five", "Six", "Seven",
                 "Eight", "Nine", "Ten", "Jack", "Queen", "King", "Ace"]

        for suit in suits:
            for rank in ranks:
                new_card = Card(suit, rank)
                self.deck.append(new_card)
                