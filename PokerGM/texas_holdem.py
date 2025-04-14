import pygame
import sys
import random
from pygame.locals import *

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TABLE_WIDTH, TABLE_HEIGHT = 900, 450
TABLE_POS_X, TABLE_POS_Y = (SCREEN_WIDTH - TABLE_WIDTH) // 2, 100
BACKGROUND_COLOR = (7, 99, 36)  # Dark green
TABLE_COLOR = (0, 128, 0)  # Green
HIGHLIGHT_COLOR = (255, 215, 0)  # Gold
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
CARD_WIDTH, CARD_HEIGHT = 80, 120
CARD_BACK_COLOR = (30, 30, 130)  # Dark blue
FPS = 60

# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Texas Hold'em Poker")

# Fonts
title_font = pygame.font.SysFont('Arial', 48, bold=True)
button_font = pygame.font.SysFont('Arial', 28)
player_font = pygame.font.SysFont('Arial', 24)
chip_font = pygame.font.SysFont('Arial', 20)


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.color = RED if suit in ['hearts', 'diamonds'] else BLACK
        self.image = self._load_card_image()
        self.face_up = True

    def _load_card_image(self):
        rank_map = {'J': 'jack', 'Q': 'queen', 'K': 'king', 'A': 'ace'}
        rank_str = rank_map.get(self.rank, self.rank).lower()
        suit_str = self.suit.lower()
        filename = f"cards/{rank_str}_of_{suit_str}.png"
        try:
            image = pygame.image.load(filename)
            return pygame.transform.scale(image, (CARD_WIDTH, CARD_HEIGHT))
        except (pygame.error, FileNotFoundError) as e:
            print(f"Cannot load image '{filename}': {e}. Using text-based card.")
            return self._create_fallback_image()

    def _create_fallback_image(self):
        card_surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        card_surface.fill(WHITE)
        pygame.draw.rect(card_surface, BLACK, (0, 0, CARD_WIDTH, CARD_HEIGHT), 2)
        rank_text = chip_font.render(self.rank, True, self.color)
        suit_text = chip_font.render(self.suit[0].upper(), True, self.color)
        card_surface.blit(rank_text, (5, 5))
        card_surface.blit(suit_text, (CARD_WIDTH - 15, CARD_HEIGHT - 20))
        return card_surface

    def draw(self, screen, x, y):
        if self.face_up:
            screen.blit(self.image, (x, y))
        else:
            card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            card_back.fill(CARD_BACK_COLOR)
            pygame.draw.rect(card_back, WHITE, (0, 0, CARD_WIDTH, CARD_HEIGHT), 2)
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
        x, y = self.position
        # Draw name and chips
        if self.active:
            name_text = player_font.render(f"{self.name}: ${self.chips}", True, WHITE)
            screen.blit(name_text, (x - name_text.get_width() // 2, y - 40))
        # Draw bet
        if self.current_bet > 0:
            bet_text = chip_font.render(f"Bet: ${self.current_bet}", True, WHITE)
            screen.blit(bet_text, (x - bet_text.get_width() // 2, y - 20))
        # Draw cards
        if self.cards and self.active:
            for i, card in enumerate(self.cards):
                card_x = x - CARD_WIDTH - 10 if i == 0 else x + 10
                card.face_up = self.is_human or self.show_cards
                card.draw(screen, card_x - CARD_WIDTH // 2, y)


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        text_surface = button_font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        return event.type == MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(pos)


class PokerGame:
    def __init__(self):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = "menu"
        self.num_players = 0
        self.human_player = None
        self.bot_players = []
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
        self.setup_menu()

    def create_deck(self):
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [Card(rank, suit) for suit in suits for rank in ranks]

    def setup_menu(self):
        self.buttons = []
        btn_y = SCREEN_HEIGHT // 2 - 100
        for i, text in enumerate(["Dual (1v1)", "Three Players", "Four Players", "Five Players", "Exit"]):
            x = SCREEN_WIDTH // 2 - 100
            y = btn_y + i * 80
            color = RED if text == "Exit" else HIGHLIGHT_COLOR
            hover_color = (255, 100, 100) if text == "Exit" else (255, 255, 150)
            self.buttons.append(Button(x, y, 200, 60, text, color, hover_color))

    def setup_action_buttons(self):
        self.action_buttons = []
        btn_x = SCREEN_WIDTH // 2 - 160
        for i, text in enumerate(["Call", "Raise", "Fold"]):
            x = btn_x + i * 110
            color = RED if text == "Fold" else HIGHLIGHT_COLOR
            hover_color = (255, 100, 100) if text == "Fold" else (255, 255, 150)
            self.action_buttons.append(Button(x, SCREEN_HEIGHT - 80, 100, 50, text, color, hover_color))
        self.quit_button = Button(20, 20, 100, 40, "Menu", RED, (255, 100, 100))

    def start_game(self, num_players):
        self.state = "game"
        self.num_players = num_players
        self.human_player = Player("You", is_human=True)
        self.bot_players = [Player(f"Bot {i + 1}") for i in range(num_players - 1)]
        self.all_players = [self.human_player] + self.bot_players
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
        left_edge_x = TABLE_POS_X + 50
        right_edge_x = TABLE_POS_X + TABLE_WIDTH - 50
        top_edge_y = TABLE_POS_Y - 40
        middle_y = TABLE_POS_Y + TABLE_HEIGHT // 2
        bottom_edge_y = TABLE_POS_Y + TABLE_HEIGHT + 40  # Below table

        human_x = TABLE_POS_X + TABLE_WIDTH // 2
        self.human_player.position = (human_x, bottom_edge_y)

        if self.num_players == 2:
            self.bot_players[0].position = (human_x, top_edge_y)
        elif self.num_players == 3:
            self.bot_players[0].position = (right_edge_x, middle_y)
            self.bot_players[1].position = (left_edge_x, middle_y)
        elif self.num_players == 4:
            self.bot_players[0].position = (right_edge_x, bottom_edge_y)
            self.bot_players[1].position = (left_edge_x, bottom_edge_y)
            self.bot_players[2].position = (human_x, top_edge_y)
        elif self.num_players == 5:
            self.bot_players[0].position = (right_edge_x, bottom_edge_y)
            self.bot_players[1].position = (left_edge_x, bottom_edge_y)
            self.bot_players[2].position = (right_edge_x, middle_y)
            self.bot_players[3].position = (left_edge_x, middle_y)

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
            player.cards = [self.deck.pop(), self.deck.pop()]

        self.message = "Place your bets!"
        self.message_timer = pygame.time.get_ticks() + 2000
        self.start_betting_round()

    def start_betting_round(self):
        self.current_player = self.find_first_active_player()
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
        self.all_players[self.current_player].folded = True
        self.message = "You folded"
        self.message_timer = pygame.time.get_ticks() + 2000
        self.next_player()

    def bot_decision(self):
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
        next_player = (self.current_player + 1) % len(self.all_players)
        while (self.all_players[next_player].folded or not self.all_players[next_player].active) and next_player != self.current_player:
            next_player = (next_player + 1) % len(self.all_players)

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
            self.deck.pop()  # Burn card
            self.community_cards.extend([self.deck.pop() for _ in range(3)])
            self.message = "Flop dealt!"
        elif len(self.community_cards) == 3:
            self.deck.pop()  # Burn card
            self.community_cards.append(self.deck.pop())
            self.message = "Turn dealt!"
        elif len(self.community_cards) == 4:
            self.deck.pop()  # Burn card
            self.community_cards.append(self.deck.pop())
            self.message = "River dealt!"

        self.message_timer = pygame.time.get_ticks() + 2000
        if len(self.community_cards) == 5:
            self.showdown()
        else:
            self.current_player = self.find_first_active_player()
            self.start_betting_round()

    def showdown(self):
        active_players = [p for p in self.all_players if not p.folded and p.active]
        for player in active_players:
            player.show_cards = True
        winner = active_players[0] if active_players else self.all_players[0]
        self.message = f"{winner.name} wins ${self.pot}!"
        winner.chips += self.pot
        self.pot = 0
        self.message_timer = pygame.time.get_ticks() + 3000
        pygame.time.set_timer(USEREVENT + 2, 3000)

    def draw_menu(self):
        self.screen.fill(BACKGROUND_COLOR)
        title_text = title_font.render("Texas Hold'em Poker", True, HIGHLIGHT_COLOR)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
        subtitle_text = button_font.render("Select Number of Players", True, WHITE)
        self.screen.blit(subtitle_text, (SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2, 220))
        for button in self.buttons:
            button.draw(self.screen)

    def draw_game(self):
        self.screen.fill(BACKGROUND_COLOR)
        # Draw table
        pygame.draw.rect(self.screen, TABLE_COLOR, (TABLE_POS_X, TABLE_POS_Y, TABLE_WIDTH, TABLE_HEIGHT), border_radius=20)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, (TABLE_POS_X, TABLE_POS_Y, TABLE_WIDTH, TABLE_HEIGHT), 5, border_radius=20)
        # Draw pot
        pot_text = player_font.render(f"Pot: ${self.pot}", True, WHITE)
        self.screen.blit(pot_text, (SCREEN_WIDTH // 2 - pot_text.get_width() // 2, TABLE_POS_Y + 20))
        # Draw community cards
        community_x = TABLE_POS_X + (TABLE_WIDTH - CARD_WIDTH * 5 - 40) // 2
        community_y = TABLE_POS_Y + (TABLE_HEIGHT - CARD_HEIGHT) // 2
        if self.community_cards:
            pygame.draw.rect(self.screen, (0, 80, 0), (community_x - 10, community_y - 10, CARD_WIDTH * 5 + 40, CARD_HEIGHT + 20), border_radius=10)
        for i, card in enumerate(self.community_cards):
            card.draw(self.screen, community_x + i * (CARD_WIDTH + 10), community_y)
        # Draw players
        for i, player in enumerate(self.all_players):
            player.draw(self.screen)
            if i == self.current_player and player.active and not self.game_over:
                x, y = player.position
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (x, y - 60), 15, 2)
        # Draw message
        if self.message and (self.message_timer == 0 or pygame.time.get_ticks() < self.message_timer):
            msg_text = player_font.render(self.message, True, WHITE)
            self.screen.blit(msg_text, (SCREEN_WIDTH // 2 - msg_text.get_width() // 2, SCREEN_HEIGHT - 120))
        # Draw buttons
        if not self.game_over:
            if self.all_players[self.current_player].is_human and len(self.community_cards) < 5:
                for button in self.action_buttons:
                    button.draw(self.screen)
        else:
            result_text = title_font.render(self.message, True, HIGHLIGHT_COLOR)
            self.screen.blit(result_text, (SCREEN_WIDTH // 2 - result_text.get_width() // 2, SCREEN_HEIGHT // 2))
            menu_btn = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, 200, 60, "Main Menu", HIGHLIGHT_COLOR, (255, 255, 150))
            menu_btn.draw(self.screen)
            return menu_btn
        self.quit_button.draw(self.screen)

    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            menu_btn = None
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == VIDEORESIZE:
                    self.screen = pygame.display.set_mode((max(event.w, 800), max(event.h, 600)), pygame.RESIZABLE)
                    global SCREEN_WIDTH, SCREEN_HEIGHT, TABLE_POS_X
                    SCREEN_WIDTH, SCREEN_HEIGHT = self.screen.get_size()
                    TABLE_POS_X = (SCREEN_WIDTH - TABLE_WIDTH) // 2
                elif event.type == MOUSEMOTION:
                    for button in self.buttons + self.action_buttons + ([self.quit_button] if self.quit_button else []):
                        button.check_hover(mouse_pos)
                elif event.type == MOUSEBUTTONDOWN:
                    if self.state == "menu":
                        for i, button in enumerate(self.buttons):
                            if button.is_clicked(mouse_pos, event):
                                if i == 0:
                                    self.start_game(2)
                                elif i == 1:
                                    self.start_game(3)
                                elif i == 2:
                                    self.start_game(4)
                                elif i == 3:
                                    self.start_game(5)
                                elif i == 4:
                                    running = False
                    elif self.state == "game":
                        if self.quit_button and self.quit_button.is_clicked(mouse_pos, event):
                            self.state = "menu"
                            self.setup_menu()
                            pygame.time.set_timer(USEREVENT + 1, 0)
                            pygame.time.set_timer(USEREVENT + 2, 0)
                        elif self.game_over:
                            menu_btn = self.draw_game()
                            if menu_btn and menu_btn.is_clicked(mouse_pos, event):
                                self.state = "menu"
                                self.setup_menu()
                        elif self.all_players[self.current_player].is_human and len(self.community_cards) < 5:
                            for i, button in enumerate(self.action_buttons):
                                if button.is_clicked(mouse_pos, event):
                                    if i == 0:
                                        self.human_call()
                                    elif i == 1:
                                        self.human_raise()
                                    elif i == 2:
                                        self.human_fold()
                elif event.type == USEREVENT + 1:
                    pygame.time.set_timer(USEREVENT + 1, 0)
                    self.bot_decision()
                elif event.type == USEREVENT + 2:
                    pygame.time.set_timer(USEREVENT + 2, 0)
                    self.deal_hand()

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "game":
                self.draw_game()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = PokerGame()
    game.run()