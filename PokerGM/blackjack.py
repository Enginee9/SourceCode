import pygame
import random
import sys
import time
from typing import List, Tuple

# Initialize pygame
pygame.init()

# Constants
GREEN = (53, 101, 77)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)  # Changed to match menu's dark smoky background
RED = (255, 50, 50)   # Adjusted to match Devil's dialogue color
GOLD = (255, 215, 0)
DARK_RED = (150, 0, 0)
GRAY = (200, 200, 200)  # Matches Man's dialogue color
FPS = 60
MIN_WIDTH = 800
MIN_HEIGHT = 600
HEART_ICON = "♥"
INITIAL_HEARTS = 5
WIN_REWARD = 100000

class Card:
    def __init__(self, suit: str, rank: str, screen_width: int, screen_height: int):
        self.suit = suit.lower()
        self.rank = rank.lower()
        self.value = self.get_value()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = self.load_image()
        self.x = 0
        self.y = 0

    def get_value(self) -> int:
        if self.rank in ['jack', 'queen', 'king']:
            return 10
        elif self.rank == 'ace':
            return 11
        else:
            return int(self.rank) if self.rank.isdigit() else 0

    def load_image(self):
        rank_map = {
            '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
            '7': '7', '8': '8', '9': '9', '10': '10',
            'jack': 'jack', 'queen': 'queen', 'king': 'king', 'ace': 'ace'
        }
        suit_map = {
            'clubs': 'clubs', 'diamonds': 'diamonds',
            'hearts': 'hearts', 'spades': 'spades'
        }
        card_width = int(self.screen_width * 0.1)
        card_height = int(self.screen_height * 0.2)

        filename = f"{rank_map[self.rank]}_of_{suit_map[self.suit]}.jpg"  # Changed to .png based on memory
        try:
            image = pygame.image.load(f"cards/{filename}")
            return pygame.transform.scale(image, (card_width, card_height))
        except:
            print(f"Image not found: {filename}, using fallback")
            return self.create_fallback_image(card_width, card_height)

    def create_fallback_image(self, card_width, card_height):
        font = pygame.font.SysFont('Arial', int(self.screen_height * 0.04))
        text = f"{self.rank[0]}{self.suit[0]}"
        image = pygame.Surface((card_width, card_height))
        image.fill(WHITE)
        pygame.draw.rect(image, BLACK, (0, 0, card_width, card_height), 2)
        text_surface = font.render(text, True, BLACK)
        text_rect = text_surface.get_rect(center=(card_width // 2, card_height // 2))
        image.blit(text_surface, text_rect)
        return image

    def update_size(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = self.load_image()

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))

class DeckManager:
    def __init__(self, screen_width: int, screen_height: int):
        self.deck = []
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.create_deck()
        self.shuffle_deck()

    def create_deck(self):
        suits = ["Clubs", "Diamonds", "Hearts", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        for suit in suits:
            for rank in ranks:
                self.deck.append(Card(suit, rank, self.screen_width, self.screen_height))

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def deal_card(self, target_x, target_y) -> Card:
        card = self.deck.pop()
        card.x = target_x
        card.y = target_y
        return card

class BlackjackGame:
    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.clock = pygame.time.Clock()
        self.update_sizes()
        self.deck_manager = DeckManager(self.screen_width, self.screen_height)
        self.player_hand = []
        self.dealer_hand = []
        self.game_state = "playing"
        self.message = ""
        self.loading = False
        self.hearts = INITIAL_HEARTS
        self.money = 0
        self.load_card_back()
        self.reset_game()
        # Flicker effect for ending sequence
        self.flicker = [255, 200, 255, 180, 255]  # Matches menu.py
        self.flicker_index = 0
        self.flicker_timer = 0

    def update_sizes(self):
        self.screen_width = max(MIN_WIDTH, self.screen.get_width())
        self.screen_height = max(MIN_HEIGHT, self.screen.get_height())
        self.font = pygame.font.SysFont('Arial', int(self.screen_height * 0.05))
        self.small_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.04))
        self.heart_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.08))
        self.money_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.06))
        self.dialogue_font = pygame.font.SysFont('Arial', 28, bold=True)  # Matches menu.py
        self.card_width = int(self.screen_width * 0.1)
        self.card_height = int(self.screen_height * 0.2)
        self.loading_size = int(self.screen_height * 0.15)

    def reposition_cards(self):
        card_spacing = self.card_width + 10
        for i, card in enumerate(self.player_hand):
            card.x = int(self.screen_width * 0.05) + i * card_spacing
            card.y = int(self.screen_height * 0.6)
            card.update_size(self.screen_width, self.screen_height)
        for i, card in enumerate(self.dealer_hand):
            card.x = int(self.screen_width * 0.05) + i * card_spacing
            card.y = int(self.screen_height * 0.15)
            card.update_size(self.screen_width, self.screen_height)

    def load_card_back(self):
        global CARD_BACK
        try:
            back_image = pygame.image.load("cards/card_back.jpg")  # Changed to .png
            CARD_BACK = pygame.transform.scale(back_image, (self.card_width, self.card_height))
        except:
            print("Card back image not found")
            CARD_BACK = pygame.Surface((self.card_width, self.card_height))
            CARD_BACK.fill((70, 70, 255))
            pygame.draw.rect(CARD_BACK, BLACK, (0, 0, self.card_width, self.card_height), 2)

    def reset_game(self):
        if len(self.deck_manager.deck) < 15:
            self.deck_manager = DeckManager(self.screen_width, self.screen_height)

        if self.hearts <= 0:
            self.game_state = "showing_ending"
            return

        self.player_hand = []
        self.dealer_hand = []
        self.deal_initial_cards()
        self.game_state = "playing"
        self.message = "Hit or Stand?"
        self.loading = False
        pygame.time.delay(200)

    def deal_initial_cards(self):
        card_spacing = self.card_width + 10
        card = self.deck_manager.deal_card(int(self.screen_width * 0.05), int(self.screen_height * 0.6))
        self.player_hand.append(card)
        card = self.deck_manager.deal_card(int(self.screen_width * 0.05), int(self.screen_height * 0.15))
        self.dealer_hand.append(card)
        card = self.deck_manager.deal_card(int(self.screen_width * 0.05) + card_spacing, int(self.screen_height * 0.6))
        self.player_hand.append(card)
        card = self.deck_manager.deal_card(int(self.screen_width * 0.05) + card_spacing, int(self.screen_height * 0.15))
        self.dealer_hand.append(card)

    def calculate_hand_value(self, hand: List[Card]) -> int:
        value = 0
        aces = 0
        for card in hand:
            value += card.value
            if card.rank == "ace":
                aces += 1
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value

    def show_loading(self):
        loading_rect = pygame.Rect(
            self.screen_width - self.loading_size - int(self.screen_width * 0.02),
            self.screen_height - self.loading_size - int(self.screen_height * 0.02),
            self.loading_size,
            self.loading_size
        )
        pygame.draw.arc(self.screen, WHITE, loading_rect, time.time() % 2 * 3.14, (time.time() % 2 + 0.5) * 3.14, 5)
        pygame.display.flip()
        time.sleep(0.3)

    def player_hit(self):
        if self.loading:
            return
        self.loading = True
        self.show_loading()
        self.loading = False

        x_pos = int(self.screen_width * 0.05) + len(self.player_hand) * (self.card_width + 10)
        new_card = self.deck_manager.deal_card(x_pos, int(self.screen_height * 0.6))
        self.player_hand.append(new_card)

        if len(self.player_hand) >= 5 and self.calculate_hand_value(self.player_hand) <= 21:
            self.money += WIN_REWARD
            self.game_state = "game_over"
            self.message = f"5-Card Charlie! Player wins ${WIN_REWARD:,}!"
            return

        player_value = self.calculate_hand_value(self.player_hand)
        if player_value > 21:
            self.hearts -= 1
            self.game_state = "game_over"
            self.message = f"Player busts! Lost a heart! ({self.hearts} ♥ left)"
            if self.hearts <= 0:
                self.game_state = "showing_ending"
                return
        elif player_value == 21:
            self.player_stand()

    def player_stand(self):
        self.game_state = "dealer_turn"
        self.dealer_play()

    def dealer_play(self):
        self.show_loading()
        while self.calculate_hand_value(self.dealer_hand) < 17:
            x_pos = int(self.screen_width * 0.05) + len(self.dealer_hand) * (self.card_width + 10)
            new_card = self.deck_manager.deal_card(x_pos, int(self.screen_height * 0.15))
            self.dealer_hand.append(new_card)
            self.show_loading()

        dealer_value = self.calculate_hand_value(self.dealer_hand)
        player_value = self.calculate_hand_value(self.player_hand)

        if dealer_value > 21:
            self.money += WIN_REWARD
            self.message = f"Dealer busts! Player wins ${WIN_REWARD:,}!"
        elif dealer_value > player_value:
            self.hearts -= 1
            self.message = f"Dealer wins! Lost a heart! ({self.hearts} ♥ left)"
            if self.hearts <= 0:
                self.game_state = "showing_ending"
                return
        elif dealer_value < player_value:
            self.money += WIN_REWARD
            self.message = f"Player wins! Earned ${WIN_REWARD:,}!"
        else:
            self.message = "Push! It's a tie."

        self.game_state = "game_over"

    def render_dialogue_text(self, text, speaker, y_offset):
        """Render dialogue text with speaker label and appropriate color."""
        # Colors to match menu.py
        color = (
            GRAY if speaker == "Man" else
            RED if speaker == "Devil" else
            (150, 150, 150) if speaker == "Whisper" else
            (180, 180, 180)  # Narration color
        )
        if speaker and speaker != "Narration":
            speaker_text = self.dialogue_font.render(f"{speaker}:", True, color)
            self.screen.blit(speaker_text, (50, y_offset))
            y_offset += 40
        # Wrap text to fit screen
        words = text.split()
        lines = []
        current_line = []
        line_width = 0
        max_width = self.screen_width - 100  # Match menu.py's 1100
        for word in words:
            word_surface = self.dialogue_font.render(word, True, color)
            word_width = word_surface.get_width()
            if line_width + word_width <= max_width:
                current_line.append(word)
                line_width += word_width + self.dialogue_font.size(" ")[0]
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                line_width = word_width + self.dialogue_font.size(" ")[0]
        lines.append(" ".join(current_line))
        for i, line in enumerate(lines):
            line_surface = self.dialogue_font.render(line, True, color)
            self.screen.blit(line_surface, (50, y_offset + i * 40))
        return y_offset + len(lines) * 40

    def show_game_over_sequence(self):
        """Display the ending sequence in the style of the intro scene."""
        dialogue = [
            ("Devil", "You lose."),
            ("Narration", "(A man jolts awake in his shabby apartment, the air heavy with regret.)"),
            ("Narration", "(The mirror reflects his face, now etched with unnatural age, hair turning gray.)"),
            ("Man", "What… did you take?"),
            ("Devil", "Time. Health. Love."),
            ("Devil", "Things you never really needed, did you?"),
            ("Devil", "All you ever wanted was money."),
            ("Narration", "(The man collapses, his piles of cash crumbling into ash.)"),
            ("Narration", "(Another night. A new gambler enters the casino.)"),
            ("Narration", "(The Devil steps out of the shadows, his smile sharp as ever.)"),
            ("Devil", "Will you be next?")
        ]
        current_dialogue_index = 0
        running = True
        skip = False

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_state = 'exit'
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        current_dialogue_index += 1
                        if current_dialogue_index >= len(dialogue):
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                        skip = True

            # Update flicker effect
            self.flicker_timer += 1
            if self.flicker_timer >= 10:
                self.flicker_index = (self.flicker_index + 1) % len(self.flicker)
                self.flicker_timer = 0

            # Draw scene
            self.screen.fill((20, 20, 20, self.flicker[self.flicker_index]))

            # Draw dialogue
            if current_dialogue_index < len(dialogue):
                speaker, text = dialogue[current_dialogue_index]
                self.render_dialogue_text(text, speaker, 300)  # Match menu.py's text position

            # Draw skip prompt
            skip_text = self.dialogue_font.render("Press SPACE to continue, ESC to skip", True, (150, 150, 150))
            self.screen.blit(skip_text, (10, self.screen_height - 40))

            pygame.display.flip()
            self.clock.tick(60)

        self.game_state = 'exit'

    def draw_game(self):
        self.screen.fill(BLACK)

        # Draw hearts and money
        hearts_text = f"Hearts: {HEART_ICON * self.hearts}"
        money_text = f"Money: ${self.money:,}"

        hearts_surface = self.heart_font.render(hearts_text, True, DARK_RED)  # Adjusted to darker red
        money_surface = self.money_font.render(money_text, True, GOLD)

        self.screen.blit(hearts_surface, (int(self.screen_width * 0.05), int(self.screen_height * 0.01)))
        self.screen.blit(money_surface, (int(self.screen_width * 0.7), int(self.screen_height * 0.02)))

        self.draw_text("Dealer's Hand:", int(self.screen_width * 0.05), int(self.screen_height * 0.08))
        for i, card in enumerate(self.dealer_hand):
            if i == 0 and self.game_state == "playing":
                self.draw_hidden_card(int(self.screen_width * 0.05) + i * (self.card_width + 10),
                                      int(self.screen_height * 0.15))
            else:
                card.draw(self.screen)

        self.draw_text("Player's Hand:", int(self.screen_width * 0.05), int(self.screen_height * 0.5))
        for card in self.player_hand:
            card.draw(self.screen)

        dealer_value = self.calculate_hand_value(self.dealer_hand) if self.game_state != "playing" else \
        self.dealer_hand[1].value
        self.draw_text(f"Dealer: {dealer_value}", int(self.screen_width * 0.75), int(self.screen_height * 0.08))
        self.draw_text(f"Player: {self.calculate_hand_value(self.player_hand)}", int(self.screen_width * 0.75),
                       int(self.screen_height * 0.5))

        self.draw_text(self.message, int(self.screen_width * 0.05), int(self.screen_height * 0.85))

        if self.game_state == "playing":
            self.draw_button("Hit", int(self.screen_width * 0.75), int(self.screen_height * 0.65),
                             int(self.screen_width * 0.15), int(self.screen_height * 0.08), self.player_hit)
            self.draw_button("Stand", int(self.screen_width * 0.75), int(self.screen_height * 0.75),
                             int(self.screen_width * 0.15), int(self.screen_height * 0.08), self.player_stand)
            self.draw_button("Menu", int(self.screen_width * 0.05), int(self.screen_height * 0.91),
                             int(self.screen_width * 0.15), int(self.screen_height * 0.08),
                             lambda: setattr(self, 'game_state', 'exit'))
        elif self.game_state == "game_over":
            if self.hearts > 0:
                self.draw_button("Play Again", int(self.screen_width * 0.75), int(self.screen_height * 0.65),
                                 int(self.screen_width * 0.15), int(self.screen_height * 0.08), self.reset_game)
            else:
                pygame.draw.rect(self.screen, (100, 100, 100), (
                int(self.screen_width * 0.75), int(self.screen_height * 0.65), int(self.screen_width * 0.15),
                int(self.screen_height * 0.08)))
                text = self.small_font.render("Play Again", True, (150, 150, 150))
                text_rect = text.get_rect(center=(int(self.screen_width * 0.75) + int(self.screen_width * 0.15) // 2,
                                                  int(self.screen_height * 0.65) + int(self.screen_height * 0.08) // 2))
                self.screen.blit(text, text_rect)

            self.draw_button("Menu", int(self.screen_width * 0.75), int(self.screen_height * 0.75),
                             int(self.screen_width * 0.15), int(self.screen_height * 0.08),
                             lambda: setattr(self, 'game_state', 'exit'))

    def draw_text(self, text: str, x: int, y: int):
        text_surface = self.font.render(text, True, WHITE)
        self.screen.blit(text_surface, (x, y))

    def draw_hidden_card(self, x: int, y: int):
        self.screen.blit(CARD_BACK, (x, y))

    def draw_button(self, text: str, x: int, y: int, width: int, height: int, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if x < mouse[0] < x + width and y < mouse[1] < y + height:
            pygame.draw.rect(self.screen, (70, 130, 180), (x, y, width, height))
            if click[0] == 1 and action is not None and not self.loading:
                action()
        else:
            pygame.draw.rect(self.screen, (100, 100, 100), (x, y, width, height))

        text_surface = self.small_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text_surface, text_rect)

    def run(self):
        while self.game_state != 'exit':
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                elif event.type == pygame.VIDEORESIZE:
                    new_width = max(MIN_WIDTH, event.w)
                    new_height = max(MIN_HEIGHT, event.h)
                    self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                    self.update_sizes()
                    self.load_card_back()
                    self.reposition_cards()

            if self.game_state == "showing_ending":
                self.show_game_over_sequence()
            else:
                self.draw_game()

            pygame.display.flip()
            self.clock.tick(60)
        return 'menu'

if __name__ == "__main__":
    screen = pygame.display.set_mode((1200, 800), pygame.RESIZABLE)  # Match menu.py resolution
    game = BlackjackGame(screen)
    game.run()