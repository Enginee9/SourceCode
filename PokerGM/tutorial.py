import pygame
from blackjack import Card

# Constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FPS = 60
MIN_WIDTH = 400  # Minimum window width
MIN_HEIGHT = 300  # Minimum window height


class BlackjackTutorial:
    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.update_sizes()
        self.running = True
        self.clock = pygame.time.Clock()

        # Load example cards for visuals
        self.example_cards = {
            "2": Card("Hearts", "2", self.screen_width, self.screen_height),
            "3": Card("Clubs", "3", self.screen_width, self.screen_height),
            "4": Card("Diamonds", "4", self.screen_width, self.screen_height),
            "5": Card("Spades", "5", self.screen_width, self.screen_height),
            "6": Card("Hearts", "6", self.screen_width, self.screen_height),
            "10": Card("Diamonds", "10", self.screen_width, self.screen_height),
            "king": Card("Spades", "King", self.screen_width, self.screen_height),
            "ace": Card("Clubs", "Ace", self.screen_width, self.screen_height)
        }

        # Tutorial content with visuals
        self.pages = [
            {
                "text": [
                    "BLACKJACK TUTORIAL",
                    "Objective: Beat the dealer by",
                    "getting a hand value closer",
                    "to 21 without going over.",
                    "",
                    "Card Values:",
                    "- 2-10 = Face value",
                    "- Face cards = 10",
                    "- Ace = 1 or 11"
                ],
                "visuals": [
                    {"card": "2", "x": int(self.screen_width * 0.55), "y": int(self.screen_height * 0.4), "label": "2 = 2"},
                    {"card": "10", "x": int(self.screen_width * 0.7), "y": int(self.screen_height * 0.4), "label": "10 = 10"},
                    {"card": "king", "x": int(self.screen_width * 0.55), "y": int(self.screen_height * 0.65), "label": "King = 10"},
                    {"card": "ace", "x": int(self.screen_width * 0.7), "y": int(self.screen_height * 0.65), "label": "Ace = 1 or 11"}
                ]
            },
            {
                "text": [
                    "Game Rules:",
                    "- You and dealer get 2 cards",
                    "- Dealer shows 1 card face up",
                    "- Hit: Take another card",
                    "- Stand: Keep your hand",
                    "",
                    "Special Wins:",
                    "- Blackjack (Ace + 10) = Win"
                ],
                "visuals": [
                    {"card": "ace", "x": int(self.screen_width * 0.55), "y": int(self.screen_height * 0.5), "label": "Player Card"},
                    {"card": "10", "x": int(self.screen_width * 0.7), "y": int(self.screen_height * 0.5), "label": "Player Card"},
                    {"card": "king", "x": int(self.screen_width * 0.55), "y": int(self.screen_height * 0.75), "label": "Dealer Hidden"},
                    {"card": "2", "x": int(self.screen_width * 0.7), "y": int(self.screen_height * 0.75), "label": "Dealer Face Up"}
                ]
            },
            {
                "text": [
                    "Advanced Rules:",
                    "- 5-Card Charlie: 5 cards",
                    "  under 21 = Win",
                    "- Dealer must hit until 17",
                    "- Bust (over 21) = Lose",
                    "",
                    "Press Esc to return to menu"
                ],
                "visuals": [
                    {"card": "2", "x": int(self.screen_width * 0.5), "y": int(self.screen_height * 0.5), "label": "2"},
                    {"card": "3", "x": int(self.screen_width * 0.55), "y": int(self.screen_height * 0.55), "label": "3"},
                    {"card": "4", "x": int(self.screen_width * 0.6), "y": int(self.screen_height * 0.6), "label": "4"},
                    {"card": "5", "x": int(self.screen_width * 0.65), "y": int(self.screen_height * 0.65), "label": "5"},
                    {"card": "6", "x": int(self.screen_width * 0.7), "y": int(self.screen_height * 0.7), "label": "6"}
                ]
            }
        ]
        self.reposition_cards(0)  # Initialize card positions

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
                card = self.example_cards[visual["card"]]
                card.x = visual["x"]
                card.y = visual["y"]
                card.update_size(self.screen_width, self.screen_height)

    def draw_page(self, page):
        self.screen.fill(BLACK)

        # Draw text on the left side
        y_pos = int(self.screen_height * 0.08)
        for i, line in enumerate(page["text"]):
            if i == 0:
                text = self.font_large.render(line, True, WHITE)
            elif line.startswith("-"):
                text = self.font_small.render(line, True, WHITE)
            else:
                text = self.font_medium.render(line, True, WHITE)
            self.screen.blit(text, (int(self.screen_width * 0.05), y_pos))
            y_pos += int(self.screen_height * 0.08) if i == 0 else int(self.screen_height * 0.06)

        # Draw visuals on the right side
        if "visuals" in page:
            for visual in page["visuals"]:
                card = self.example_cards[visual["card"]]
                card.draw(self.screen)

                label = self.font_small.render(visual["label"], True, WHITE)
                label_rect = label.get_rect(center=(visual["x"] + int(self.screen_width * 0.05), visual["y"] - int(self.screen_height * 0.03)))
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


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)  # Changed to 1920x1080
    tutorial = BlackjackTutorial(screen)
    tutorial.run()