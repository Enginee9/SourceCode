import random

def shuffle_deck(self):
    n = len(self.deck)
    while n > 1:
        n -= 1
        k = random.randint(0, n)
        self.deck[k], self.deck[n] = self.deck[n], self.deck[k]