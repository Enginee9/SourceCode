import pygame
import sys
import random
from pygame.locals import *
from itertools import combinations

# Constants
TABLE_WIDTH, TABLE_HEIGHT = 900, 450
BACKGROUND_COLOR = (0, 0, 0)  # Black
TABLE_COLOR = (0, 128, 0)  # Green
HIGHLIGHT_COLOR = (255, 215, 0)  # Gold
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
FPS = 60
MIN_WIDTH = 400
MIN_HEIGHT = 300

class Card:
    def __init__(self, rank, suit, screen_width, screen_height):
        self.rank = rank.lower()
        self.suit = suit.lower()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = self.load_image()
        self.face_up = True
        self.x = 0
        self.y = 0

    def load_image(self):
        rank_map = {
            '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
            '7': '7', '8': '8', '9': '9', '10': '10',
            'j': 'jack', 'q': 'queen', 'k': 'king', 'a': 'ace'
        }
        suit_map = {
            'hearts': 'hearts', 'diamonds': 'diamonds',
            'clubs': 'clubs', 'spades': 'spades'
        }
        card_width = int(self.screen_width * 0.0625)
        card_height = int(self.screen_height * 0.1667)

        filename = f"{rank_map.get(self.rank, self.rank)}_of_{suit_map.get(self.suit, self.suit)}.jpg"
        try:
            image = pygame.image.load(f"cards/{filename}")
            return pygame.transform.scale(image, (card_width, card_height))
        except (pygame.error, FileNotFoundError) as e:
            if not hasattr(self, '_logged_error'):
                print(f"Image not found: {filename}, using fallback")
                self._logged_error = True
            return self.create_fallback_image(card_width, card_height)

    def create_fallback_image(self, card_width, card_height):
        font = pygame.font.SysFont('Arial', int(self.screen_height * 0.0278))
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

    def draw(self, screen, x, y):
        self.x = x
        self.y = y
        if self.face_up:
            screen.blit(self.image, (x, y))
        else:
            card_back = pygame.transform.scale(PokerGame.CARD_BACK, (int(self.screen_width * 0.0625), int(self.screen_height * 0.1667)))
            screen.blit(card_back, (x, y))

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.cards = []
        self.chips = 1000
        self.current_bet = 0
        self.folded = False
        self.show_cards = False
        self.active = True
        self.position = (0, 0)

    def draw(self, screen):
        card_width = int(screen.get_width() * 0.0625)
        card_height = int(screen.get_height() * 0.1667)
        margin = int(screen.get_width() * 0.025)  # 20px at 800px
        player_font = pygame.font.SysFont('Arial', int(screen.get_height() * 0.033))
        chip_font = pygame.font.SysFont('Arial', int(screen.get_height() * 0.028))

        if self.is_human:
            # Bottom-left: Player cards
            card_y = screen.get_height() - card_height - margin
            text_y = card_y + card_height + 10
        else:
            # Top-right: Bot cards
            card_y = margin
            text_y = margin

        if self.active:
            name_text = player_font.render(f"{self.name}: ${self.chips}", True, WHITE)
            text_x = margin if self.is_human else screen.get_width() - name_text.get_width() - margin
            screen.blit(name_text, (text_x, text_y))
            text_y += 20 if self.is_human else 40

        if self.current_bet > 0:
            bet_text = chip_font.render(f"Bet: ${self.current_bet}", True, WHITE)
            text_x = margin if self.is_human else screen.get_width() - bet_text.get_width() - margin
            screen.blit(bet_text, (text_x, text_y))

        if self.cards and self.active:
            for i, card in enumerate(self.cards):
                if self.is_human:
                    card_x = margin + i * (card_width + 10)
                else:
                    card_x = screen.get_width() - card_width - margin - (1 - i) * (card_width + 10)
                card.face_up = self.is_human or self.show_cards
                card.draw(screen, card_x, card_y)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.clicked = False

    def draw(self, screen):
        button_font = pygame.font.SysFont('Arial', int(screen.get_height() * 0.039))
        color = (0, 255, 0) if self.clicked else (self.hover_color if self.is_hovered else self.color)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        text_surface = button_font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos):
            self.clicked = True
            return True
        return False

    def reset_click(self):
        self.clicked = False

class PokerGame:
    CARD_BACK = None
    HAND_RANKS = {
        'royal_flush': 10,
        'straight_flush': 9,
        'four_of_a_kind': 8,
        'full_house': 7,
        'flush': 6,
        'straight': 5,
        'three_of_a_kind': 4,
        'two_pair': 3,
        'pair': 2,
        'high_card': 1
    }

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = "menu"
        self.human_player = None
        self.bot_player = None
        self.all_players = []
        self.community_cards = []
        self.current_player = 0
        self.pot = 0
        self.current_bet = 0
        self.deck = self.create_deck()
        self.buttons = []
        self.action_buttons = []
        self.quit_button = None
        self.game_over = False
        self.message = ""
        self.message_timer = 0
        self.loading = False
        self.loading_start = 0
        self.loading_duration = 300  # ms
        self.dealer_button = 0
        self.load_card_back()
        self.update_sizes()
        self.setup_menu()

    def load_card_back(self):
        try:
            back_image = pygame.image.load("cards/card_back.jpg")
            PokerGame.CARD_BACK = pygame.transform.scale(back_image, (int(self.screen.get_width() * 0.0625), int(self.screen.get_height() * 0.1667)))
        except (pygame.error, FileNotFoundError):
            if not hasattr(self, '_logged_back_error'):
                print("Card back image not found, using fallback")
                self._logged_back_error = True
            PokerGame.CARD_BACK = pygame.Surface((int(self.screen.get_width() * 0.0625), int(self.screen.get_height() * 0.1667)))
            PokerGame.CARD_BACK.fill((70, 70, 255))
            pygame.draw.rect(PokerGame.CARD_BACK, BLACK, (0, 0, int(self.screen.get_width() * 0.0625), int(self.screen.get_height() * 0.1667)), 2)

    def update_sizes(self):
        self.screen_width, self.screen_height = self.screen.get_size()
        self.table_pos_x = (self.screen_width - TABLE_WIDTH) // 2
        self.table_pos_y = self.screen_height * 0.1389
        for card in self.community_cards:
            card.update_size(self.screen_width, self.screen_height)
        for player in self.all_players:
            for card in player.cards:
                card.update_size(self.screen_width, self.screen_height)
        self.load_card_back()

    def create_deck(self):
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
        return [Card(rank, suit, self.screen.get_width(), self.screen.get_height()) for suit in suits for rank in ranks]

    def setup_menu(self):
        self.buttons = []
        btn_y = self.screen_height // 2 - 60
        for i, text in enumerate(["Play Dual", "Exit"]):
            x = self.screen_width // 2 - 100
            y = btn_y + i * 80
            color = RED if text == "Exit" else HIGHLIGHT_COLOR
            hover_color = (255, 100, 100) if text == "Exit" else (255, 255, 150)
            self.buttons.append(Button(x, y, 200, 60, text, color, hover_color))

    def setup_action_buttons(self):
        self.action_buttons = []
        btn_x = self.screen_width // 2 - 160
        for i, text in enumerate(["Call", "Raise", "Fold"]):
            x = btn_x + i * 110
            color = RED if text == "Fold" else HIGHLIGHT_COLOR
            hover_color = (255, 100, 100) if text == "Fold" else (255, 255, 150)
            self.action_buttons.append(Button(x, self.screen_height - 80, 100, 50, text, color, hover_color))
        self.quit_button = Button(20, 20, 100, 40, "Menu", RED, (255, 100, 100))

    def show_loading(self, current_time):
        if not self.loading or current_time > self.loading_start + self.loading_duration:
            self.loading = False
            return
        loading_size = int(self.screen_height * 0.05)
        loading_rect = pygame.Rect(
            self.screen_width // 2 - loading_size // 2,
            self.screen_height // 2 - loading_size // 2,
            loading_size,
            loading_size
        )
        elapsed = (current_time - self.loading_start) / 1000
        start_angle = elapsed * 3.14
        end_angle = (elapsed + 0.5) * 3.14
        pygame.draw.arc(self.screen, WHITE, loading_rect, start_angle, end_angle, 3)

    def start_game(self):
        self.state = "game"
        self.human_player = Player("You", is_human=True)
        self.bot_player = Player("Bot")
        self.all_players = [self.human_player, self.bot_player]
        self.dealer_button = 0
        self.set_player_positions()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_player = 0
        self.game_over = False
        self.message = "New hand started!"
        self.message_timer = pygame.time.get_ticks() + 2000
        self.setup_action_buttons()
        self.deal_hand()

    def set_player_positions(self):
        pass  # Card positions handled in Player.draw

    def deal_hand(self):
        self.all_players = [p for p in self.all_players if p.chips > 0]
        if len([p for p in self.all_players if p.is_human]) == 0:
            self.game_over = True
            self.message = "Game Over: You ran out of chips!"
            self.message_timer = 0
            return
        if len(self.all_players) == 1:
            self.game_over = True
            self.message = f"{self.all_players[0].name} wins the game!"
            self.message_timer = 0
            return

        self.community_cards = []
        self.current_bet = 0
        for player in self.all_players:
            player.cards = []
            player.current_bet = 0
            player.folded = False
            player.show_cards = False
            player.active = True

        random.shuffle(self.deck)
        for player in self.all_players:
            card1 = self.deck.pop()
            card2 = self.deck.pop()
            card1.update_size(self.screen_width, self.screen_height)
            card2.update_size(self.screen_width, self.screen_height)
            player.cards = [card1, card2]

        # Post blinds
        small_blind_idx = (self.dealer_button + 1) % 2
        big_blind_idx = (self.dealer_button + 0) % 2  # In heads-up, dealer is small blind
        small_blind_amount = 10
        big_blind_amount = 20
        small_blind_player = self.all_players[small_blind_idx]
        big_blind_player = self.all_players[big_blind_idx]
        if small_blind_player.chips > 0:
            small_blind_player.chips -= min(small_blind_amount, small_blind_player.chips)
            small_blind_player.current_bet = min(small_blind_amount, small_blind_player.chips)
            self.pot += min(small_blind_amount, small_blind_player.chips)
        if big_blind_player.chips > 0:
            big_blind_player.chips -= min(big_blind_amount, big_blind_player.chips)
            big_blind_player.current_bet = min(big_blind_amount, big_blind_player.chips)
            self.pot += min(big_blind_amount, big_blind_player.chips)
            self.current_bet = big_blind_player.current_bet
        if small_blind_player.chips <= 0:
            small_blind_player.active = False
        if big_blind_player.chips <= 0:
            big_blind_player.active = False

        self.message = "Blinds posted! Place your bets!"
        self.message_timer = pygame.time.get_ticks() + 2000
        self.start_betting_round()

    def start_betting_round(self):
        if len(self.community_cards) == 0:  # Pre-flop
            self.current_player = self.dealer_button  # Big blind (non-dealer) acts first pre-flop
        else:  # Flop, Turn, River
            self.current_player = (self.dealer_button + 1) % 2  # Small blind (dealer) acts first post-flop
        while (self.all_players[self.current_player].folded or not self.all_players[self.current_player].active):
            self.current_player = (self.current_player + 1) % 2
        if self.all_players[self.current_player].is_human:
            self.message = "Your turn: Call, Raise, or Fold"
            self.message_timer = pygame.time.get_ticks() + 5000
        else:
            pygame.time.set_timer(USEREVENT + 1, 1000)

    def find_first_active_player(self):
        for i, player in enumerate(self.all_players):
            if not player.folded and player.active:
                return i
        return 0

    def human_call(self):
        if self.loading:
            return
        self.loading = True
        self.loading_start = pygame.time.get_ticks()

        player = self.all_players[self.current_player]
        amount = min(self.current_bet - player.current_bet, player.chips)
        player.chips -= amount
        player.current_bet += amount
        self.pot += amount
        if player.chips <= 0:
            player.active = False
        self.message = f"You called ${amount}"
        self.message_timer = pygame.time.get_ticks() + 2000
        self.next_player()

    def human_raise(self):
        if self.loading:
            return
        self.loading = True
        self.loading_start = pygame.time.get_ticks()

        player = self.all_players[self.current_player]
        amount = min(50, player.chips)
        player.chips -= amount
        player.current_bet += amount
        self.pot += amount
        self.current_bet = player.current_bet
        if player.chips <= 0:
            player.active = False
        self.message = f"You raised by ${amount}"
        self.message_timer = pygame.time.get_ticks() + 2000
        self.next_player()

    def human_fold(self):
        if self.loading:
            return
        self.loading = True
        self.loading_start = pygame.time.get_ticks()

        self.all_players[self.current_player].folded = True
        self.message = "You folded"
        self.message_timer = pygame.time.get_ticks() + 2000
        self.next_player()

    def bot_decision(self):
        self.loading = True
        self.loading_start = pygame.time.get_ticks()

        player = self.all_players[self.current_player]
        if random.random() < 0.1 and self.current_bet > 0:
            decision = 'fold'
        elif self.current_bet == 0 or random.random() < 0.7:
            decision = 'raise' if random.random() < 0.5 else 'call'
        else:
            decision = 'call'

        if decision == 'call' and self.current_bet > 0:
            amount = min(self.current_bet - player.current_bet, player.chips)
            player.chips -= amount
            player.current_bet += amount
            self.pot += amount
            self.message = f"{player.name} called ${amount}"
        elif decision == 'raise':
            amount = min(50, player.chips)
            player.chips -= amount
            player.current_bet += amount
            self.pot += amount
            self.current_bet = player.current_bet
            self.message = f"{player.name} raised by ${amount}"
        elif decision == 'fold':
            player.folded = True
            self.message = f"{player.name} folded"

        if player.chips <= 0:
            player.active = False
        self.message_timer = pygame.time.get_ticks() + 2000
        self.next_player()

    def next_player(self):
        next_player = (self.current_player + 1) % 2
        while (self.all_players[next_player].folded or not self.all_players[next_player].active) and next_player != self.current_player:
            next_player = (next_player + 1) % 2

        self.current_player = next_player
        if self.check_betting_round_complete():
            self.next_stage()
        else:
            self.start_betting_round()

    def check_betting_round_complete(self):
        active_players = [p for p in self.all_players if not p.folded and p.active]
        if len(active_players) < 2:
            return True
        return all(p.current_bet == self.current_bet for p in active_players)

    def next_stage(self):
        for player in self.all_players:
            player.current_bet = 0
        self.current_bet = 0

        if len(self.community_cards) == 0:
            if self.deck:
                self.deck.pop()  # Burn card
            self.community_cards.extend([self.deck.pop() for _ in range(3) if self.deck])
            for card in self.community_cards:
                card.update_size(self.screen_width, self.screen_height)
            self.message = "Flop dealt!"
        elif len(self.community_cards) == 3:
            if self.deck:
                self.deck.pop()  # Burn card
            if self.deck:
                card = self.deck.pop()
                card.update_size(self.screen_width, self.screen_height)
                self.community_cards.append(card)
            self.message = "Turn dealt!"
        elif len(self.community_cards) == 4:
            if self.deck:
                self.deck.pop()  # Burn card
            if self.deck:
                card = self.deck.pop()
                card.update_size(self.screen_width, self.screen_height)
                self.community_cards.append(card)
            self.message = "River dealt!"

        self.message_timer = pygame.time.get_ticks() + 2000
        if len(self.community_cards) == 5:
            self.showdown()
        else:
            self.current_player = self.find_first_active_player()
            self.start_betting_round()

    def evaluate_hand(self, player):
        all_cards = player.cards + self.community_cards
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
                       'jack': 11, 'queen': 12, 'king': 13, 'ace': 14}

        def is_flush(cards):
            suits = [card.suit for card in cards]
            return any(suits.count(suit) >= 5 for suit in set(suits))

        def is_straight(cards):
            values = sorted([rank_values[card.rank] for card in cards], reverse=True)
            if 14 in values:
                values.append(1)  # Ace as 1
            values = sorted(set(values), reverse=True)
            for i in range(len(values) - 4):
                if values[i] - values[i + 4] == 4:
                    return values[i]
            return 0

        def get_counts(cards):
            counts = {}
            for card in cards:
                counts[card.rank] = counts.get(card.rank, 0) + 1
            return sorted([(count, rank_values[rank]) for rank, count in counts.items()], reverse=True)

        best_rank = 'high_card'
        best_values = []

        for hand in combinations(all_cards, 5):
            hand = list(hand)
            flush = is_flush(hand)
            straight_high = is_straight(hand)
            counts = get_counts(hand)
            count_values = [(count, val) for count, val in counts]
            values = sorted([rank_values[card.rank] for card in hand], reverse=True)

            if flush and straight_high == 14 and min([rank_values[card.rank] for card in hand]) == 10:
                return ('royal_flush', [14])

            if flush and straight_high:
                return ('straight_flush', [straight_high])

            if count_values[0][0] == 4:
                kicker = [v for c, v in count_values if c == 1][0] if len(count_values) > 1 else values[-1]
                return ('four_of_a_kind', [count_values[0][1], kicker])

            if count_values[0][0] == 3 and len(count_values) > 1 and count_values[1][0] >= 2:
                return ('full_house', [count_values[0][1], count_values[1][1]])

            if flush:
                return ('flush', values[:5])

            if straight_high:
                return ('straight', [straight_high])

            if count_values[0][0] == 3:
                kickers = [v for c, v in count_values if c == 1][:2]
                return ('three_of_a_kind', [count_values[0][1]] + kickers)

            if count_values[0][0] == 2 and len(count_values) > 1 and count_values[1][0] == 2:
                kicker = [v for c, v in count_values if c == 1][0] if sum(c for c, _ in count_values) < 8 else values[-1]
                return ('two_pair', [count_values[0][1], count_values[1][1], kicker])

            if count_values[0][0] == 2:
                kickers = [v for c, v in count_values if c == 1][:3]
                return ('pair', [count_values[0][1]] + kickers)

            if values[:5] > best_values:
                best_values = values[:5]

        return (best_rank, best_values)

    def compare_hands(self, hand1, hand2):
        rank1, values1 = hand1
        rank2, values2 = hand2
        if self.HAND_RANKS[rank1] != self.HAND_RANKS[rank2]:
            return self.HAND_RANKS[rank1] - self.HAND_RANKS[rank2]
        for v1, v2 in zip(values1, values2):
            if v1 != v2:
                return v1 - v2
        return 0

    def showdown(self):
        active_players = [p for p in self.all_players if not p.folded and p.active]
        if not active_players:
            self.message = "No active players, pot remains!"
            self.message_timer = pygame.time.get_ticks() + 3000
            pygame.time.set_timer(USEREVENT + 2, 3000)
            return
        for player in active_players:
            player.show_cards = True
        hands = [(player, self.evaluate_hand(player)) for player in active_players]
        max_hand = max(hands, key=lambda x: (self.HAND_RANKS[x[1][0]], x[1][1]))
        winners = [player for player, hand in hands if self.compare_hands(hand, max_hand[1]) == 0]
        pot_share = self.pot / len(winners)
        for winner in winners:
            winner.chips += pot_share
        self.message = f"{', '.join(w.name for w in winners)} win ${pot_share:.0f} each!" if len(winners) > 1 else f"{winners[0].name} wins ${self.pot}!"
        self.pot = 0
        self.message_timer = pygame.time.get_ticks() + 3000
        pygame.time.set_timer(USEREVENT + 2, 3000)
        self.dealer_button = (self.dealer_button + 1) % 2

    def draw_menu(self):
        self.screen.fill(BACKGROUND_COLOR)
        title_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.0667), bold=True)
        button_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.0389))
        title_text = title_font.render("Texas Hold'em Poker", True, HIGHLIGHT_COLOR)
        self.screen.blit(title_text, (self.screen_width // 2 - title_text.get_width() // 2, self.screen_height * 0.2083))
        subtitle_text = button_font.render("Heads-Up Game", True, WHITE)
        self.screen.blit(subtitle_text, (self.screen_width // 2 - subtitle_text.get_width() // 2, self.screen_height * 0.3056))
        for button in self.buttons:
            button.draw(self.screen)

    def draw_game(self):
        self.screen.fill(BACKGROUND_COLOR)
        player_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.0333))
        pygame.draw.rect(self.screen, TABLE_COLOR, (self.table_pos_x, self.table_pos_y, TABLE_WIDTH, TABLE_HEIGHT), border_radius=20)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, (self.table_pos_x, self.table_pos_y, TABLE_WIDTH, TABLE_HEIGHT), 5, border_radius=20)
        pot_text = player_font.render(f"Pot: ${self.pot}", True, WHITE)
        self.screen.blit(pot_text, (self.screen_width // 2 - pot_text.get_width() // 2, self.table_pos_y + 20))
        community_x = self.table_pos_x + (TABLE_WIDTH - int(self.screen_width * 0.0625) * 5 - 40) // 2
        community_y = self.table_pos_y + (TABLE_HEIGHT - int(self.screen_height * 0.1667)) // 2
        if self.community_cards:
            pygame.draw.rect(self.screen, (0, 80, 0), (community_x - 10, community_y - 10, int(self.screen_width * 0.0625) * 5 + 40, int(self.screen_height * 0.1667) + 20), border_radius=10)
        for i, card in enumerate(self.community_cards):
            card.draw(self.screen, community_x + i * (int(self.screen_width * 0.0625) + 10), community_y)
        for i, player in enumerate(self.all_players):
            player.draw(self.screen)
            if i == self.current_player and player.active and not self.game_over:
                x = int(self.screen_width * 0.075) if player.is_human else self.screen_width - int(self.screen_width * 0.025)
                y = self.screen_height - int(self.screen_height * 0.1667) - int(self.screen_width * 0.05) if player.is_human else int(self.screen_width * 0.075)
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (x, y), 15, 2)
            if i == self.dealer_button:
                x = int(self.screen_width * 0.075) if player.is_human else self.screen_width - int(self.screen_width * 0.025)
                y = self.screen_height - int(self.screen_height * 0.1667) - int(self.screen_width * 0.025) if player.is_human else int(self.screen_width * 0.1)
                pygame.draw.circle(self.screen, WHITE, (x, y), 10)
        if self.message and (self.message_timer == 0 or pygame.time.get_ticks() < self.message_timer):
            msg_text = player_font.render(self.message, True, WHITE)
            self.screen.blit(msg_text, (self.screen_width // 2 - msg_text.get_width() // 2, self.screen_height - 120))
        if not self.game_over:
            if self.all_players[self.current_player].is_human and len(self.community_cards) < 5:
                for button in self.action_buttons:
                    button.draw(self.screen)
        else:
            title_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.0667), bold=True)
            result_text = title_font.render(self.message, True, HIGHLIGHT_COLOR)
            self.screen.blit(result_text, (self.screen_width // 2 - result_text.get_width() // 2, self.screen_height // 2))
            menu_btn = Button(self.screen_width // 2 - 100, self.screen_height // 2 + 100, 200, 60, "Main Menu", HIGHLIGHT_COLOR, (255, 255, 150))
            menu_btn.draw(self.screen)
            return menu_btn
        self.quit_button.draw(self.screen)
        self.show_loading(pygame.time.get_ticks())
        return None

class TexasHoldemGame:
    def __init__(self, screen):
        self.screen = screen
        self.game = PokerGame(screen)
        self.last_click_time = 0
        self.click_cooldown = 400  # ms

    def run(self):
        running = True
        click_timer = 0
        while running:
            mouse_pos = pygame.mouse.get_pos()
            menu_btn = None
            current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == QUIT:
                    return 'quit'
                elif event.type == VIDEORESIZE:
                    self.screen = pygame.display.set_mode((max(event.w, MIN_WIDTH), max(event.h, MIN_HEIGHT)), pygame.RESIZABLE)
                    self.game.update_sizes()
                elif event.type == MOUSEMOTION:
                    for button in self.game.buttons + self.game.action_buttons + ([self.game.quit_button] if self.game.quit_button else []):
                        button.check_hover(mouse_pos)
                elif event.type == MOUSEBUTTONDOWN:
                    if current_time < self.last_click_time + self.click_cooldown:
                        continue
                    self.last_click_time = current_time
                    if self.game.state == "menu":
                        for i, button in enumerate(self.game.buttons):
                            if button.is_clicked(mouse_pos, event):
                                if i == 0:
                                    self.game.start_game()
                                elif i == 1:
                                    return 'menu'
                    elif self.game.state == "game":
                        if self.game.quit_button and self.game.quit_button.is_clicked(mouse_pos, event):
                            return 'menu'
                        elif self.game.game_over:
                            menu_btn = self.game.draw_game()
                            if menu_btn and menu_btn.is_clicked(mouse_pos, event):
                                return 'menu'
                        elif self.game.all_players[self.game.current_player].is_human and len(self.game.community_cards) < 5:
                            for i, button in enumerate(self.game.action_buttons):
                                if button.is_clicked(mouse_pos, event):
                                    if i == 0:
                                        self.game.human_call()
                                    elif i == 1:
                                        self.game.human_raise()
                                    elif i == 2:
                                        self.game.human_fold()
                                    click_timer = current_time + 300
                elif event.type == USEREVENT + 1:
                    pygame.time.set_timer(USEREVENT + 1, 0)
                    self.game.bot_decision()
                elif event.type == USEREVENT + 2:
                    pygame.time.set_timer(USEREVENT + 2, 0)
                    self.game.deal_hand()

            if click_timer and current_time > click_timer:
                for button in self.game.action_buttons:
                    button.reset_click()
                click_timer = 0

            if self.game.state == "menu":
                self.game.draw_menu()
            elif self.game.state == "game":
                self.game.draw_game()
            pygame.display.flip()
            self.game.clock.tick(FPS)
        return 'quit'