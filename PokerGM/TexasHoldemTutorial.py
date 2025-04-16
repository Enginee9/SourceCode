import pygame
from texas_holdem import Card

# Constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FPS = 60
MIN_WIDTH = 400  # Minimum window width
MIN_HEIGHT = 300  # Minimum window height


class TexasHoldemTutorial:
    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.update_sizes()
        self.running = True
        self.clock = pygame.time.Clock()

        # Load example cards for visuals
        self.example_cards = {
            "2h": Card("2", "hearts", self.screen_width, self.screen_height),
            "10d": Card("10", "diamonds", self.screen_width, self.screen_height),
            "Jc": Card("jack", "clubs", self.screen_width, self.screen_height),
            "Qs": Card("queen", "spades", self.screen_width, self.screen_height),
            "Kh": Card("king", "hearts", self.screen_width, self.screen_height),
            "As": Card("ace", "spades", self.screen_width, self.screen_height),
            "back": None  # Will be initialized in load_card_back()
        }
        self.load_card_back()

        # Tutorial content with visuals
        self.pages = [
            {
                "title": "TEXAS HOLD'EM BASICS",
                "text": [
                    "Objective: Make the best 5-card hand",
                    "using any combination of your 2 hole",
                    "cards and the 5 community cards.",
                    "",
                    "Game Flow:",
                    "- Each player gets 2 private cards",
                    "- 5 community cards dealt face up",
                    "- Betting rounds after each deal",
                    "- Showdown if multiple players remain"
                ],
                "visuals": [
                    {"card": "Jc", "x": 0.4, "y": 0.4, "label": "Your Card"},
                    {"card": "Qs", "x": 0.5, "y": 0.4, "label": "Your Card"},
                    {"card": "back", "x": 0.7, "y": 0.4, "label": "Opponent Card"},
                    {"card": "back", "x": 0.8, "y": 0.4, "label": "Opponent Card"},
                    {"card": "2h", "x": 0.3, "y": 0.7, "label": "Flop"},
                    {"card": "10d", "x": 0.4, "y": 0.7, "label": "Flop"},
                    {"card": "Kh", "x": 0.5, "y": 0.7, "label": "Flop"}
                ]
            },
            {
                "title": "HAND RANKINGS",
                "text": [
                    "Hands from strongest to weakest:",
                    "- Royal Flush: A-K-Q-J-10 same suit",
                    "- Straight Flush: 5 sequential same suit",
                    "- Four of a Kind: Four same rank",
                    "- Full House: Three + pair",
                    "- Flush: 5 same suit",
                    "- Straight: 5 sequential",
                    "- Three of a Kind",
                    "- Two Pair",
                    "- One Pair",
                    "- High Card"
                ],
                "visuals": [
                    {"card": "As", "x": 0.5, "y": 0.3, "label": "Royal Flush"},
                    {"card": "Kh", "x": 0.6, "y": 0.3, "label": "Straight Flush"},
                    {"card": "Jc", "x": 0.5, "y": 0.5, "label": "Four of a Kind"},
                    {"card": "Qs", "x": 0.6, "y": 0.5, "label": "Full House"},
                    {"card": "10d", "x": 0.5, "y": 0.7, "label": "Flush"}
                ]
            },
            {
                "title": "BETTING ROUNDS",
                "text": [
                    "Four betting rounds:",
                    "1. Pre-Flop: After receiving hole cards",
                    "2. Flop: After first 3 community cards",
                    "3. Turn: After 4th community card",
                    "4. River: After 5th community card",
                    "",
                    "Actions:",
                    "- Call: Match current bet",
                    "- Raise: Increase the bet",
                    "- Fold: Quit the hand"
                ],
                "visuals": [
                    {"card": "Jc", "x": 0.3, "y": 0.4, "label": "Pre-Flop"},
                    {"card": "Qs", "x": 0.4, "y": 0.4, "label": "Pre-Flop"},
                    {"card": "2h", "x": 0.3, "y": 0.7, "label": "Flop"},
                    {"card": "10d", "x": 0.4, "y": 0.7, "label": "Flop"},
                    {"card": "Kh", "x": 0.5, "y": 0.7, "label": "Flop"},
                    {"card": "As", "x": 0.6, "y": 0.7, "label": "Turn"},
                    {"card": "back", "x": 0.7, "y": 0.7, "label": "River"}
                ]
            },
            {
                "title": "GAME STRATEGY",
                "text": [
                    "Basic Tips:",
                    "- Play strong starting hands",
                    "- Position matters (act last = advantage)",
                    "- Watch opponents' betting patterns",
                    "- Manage your bankroll carefully",
                    "",
                    "Press Esc to return to menu",
                    "Click or press any key to continue"
                ],
                "visuals": [
                    {"card": "As", "x": 0.3, "y": 0.4, "label": "Strong Hand"},
                    {"card": "Kh", "x": 0.4, "y": 0.4, "label": "Strong Hand"},
                    {"card": "2h", "x": 0.6, "y": 0.4, "label": "Weak Hand"},
                    {"card": "10d", "x": 0.7, "y": 0.4, "label": "Weak Hand"}
                ]
            }
        ]
        self.reposition_cards(0)  # Initialize card positions

    def load_card_back(self):
        try:
            back_image = pygame.image.load("cards/card_back.jpg")
            card_width = int(self.screen_width * 0.0625)
            card_height = int(self.screen_height * 0.1667)
            self.example_cards["back"] = pygame.transform.scale(back_image, (card_width, card_height))
        except (pygame.error, FileNotFoundError):
            card_width = int(self.screen_width * 0.0625)
            card_height = int(self.screen_height * 0.1667)
            self.example_cards["back"] = pygame.Surface((card_width, card_height))
            self.example_cards["back"].fill((70, 70, 255))
            pygame.draw.rect(self.example_cards["back"], BLACK, (0, 0, card_width, card_height), 2)

    def update_sizes(self):
        self.screen_width = max(MIN_WIDTH, self.screen.get_width())
        self.screen_height = max(MIN_HEIGHT, self.screen.get_height())
        self.font_large = pygame.font.SysFont('Arial', int(self.screen_height * 0.08))
        self.font_medium = pygame.font.SysFont('Arial', int(self.screen_height * 0.05))
        self.font_small = pygame.font.SysFont('Arial', int(self.screen_height * 0.04))

    def reposition_cards(self, page_index):
        """Reposition cards for the current page based on screen size."""
        page = self.pages[page_index]
        if "visuals" in page:
            for visual in page["visuals"]:
                if visual["card"] != "back":
                    card = self.example_cards[visual["card"]]
                    card.x = int(visual["x"] * self.screen_width)
                    card.y = int(visual["y"] * self.screen_height)
                    card.update_size(self.screen_width, self.screen_height)

    def draw_page(self, page):
        self.screen.fill(BLACK)

        # Draw title
        title = self.font_large.render(page["title"], True, WHITE)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, int(self.screen_height * 0.05)))

        # Draw text on the left side
        y_pos = int(self.screen_height * 0.15)
        for line in page["text"]:
            if line.startswith("-"):
                text = self.font_small.render(line, True, WHITE)
            else:
                text = self.font_medium.render(line, True, WHITE)
            self.screen.blit(text, (int(self.screen_width * 0.05), y_pos))
            y_pos += int(self.screen_height * 0.05)

        # Draw visuals on the right side
        if "visuals" in page:
            for visual in page["visuals"]:
                x_pos = int(visual["x"] * self.screen_width)
                y_pos = int(visual["y"] * self.screen_height)

                if visual["card"] == "back":
                    self.screen.blit(self.example_cards["back"], (x_pos, y_pos))
                else:
                    card = self.example_cards[visual["card"]]
                    card.draw(self.screen, x_pos, y_pos)

                label = self.font_small.render(visual["label"], True, WHITE)
                label_rect = label.get_rect(
                    center=(x_pos + int(self.screen_width * 0.05), y_pos - int(self.screen_height * 0.03)))
                self.screen.blit(label, label_rect)

    def run(self):
        current_page = 0

        while self.running:
            self.draw_page(self.pages[current_page])
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                elif event.type == pygame.VIDEORESIZE:
                    new_width = max(MIN_WIDTH, event.w)
                    new_height = max(MIN_HEIGHT, event.h)
                    self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                    self.update_sizes()
                    self.reposition_cards(current_page)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'menu'
                    else:
                        current_page = (current_page + 1) % len(self.pages)
                        self.reposition_cards(current_page)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    current_page = (current_page + 1) % len(self.pages)
                    self.reposition_cards(current_page)

            self.clock.tick(FPS)

        return 'menu'