import pygame
import sys
from blackjack import BlackjackGame
from texas_holdem import TexasHoldemGame
from tutorial import BlackjackTutorial

# Constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class MainMenu:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)  # Start resizable
        pygame.display.set_caption("Card Games")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 48)
        self.small_font = pygame.font.SysFont('Arial', 32)
        self.screen_width, self.screen_height = self.screen.get_size()

    def update_sizes(self):
        """Update dimensions when window is resized."""
        self.screen_width, self.screen_height = self.screen.get_size()
        # Scale fonts based on window size
        self.font = pygame.font.SysFont('Arial', int(self.screen_height * 0.08))
        self.small_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.05))

    def draw(self):
        self.screen.fill(BLACK)

        # Draw title
        title = self.font.render("POKER", True, WHITE)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, int(self.screen_height * 0.15)))

        # Draw buttons with relative positions
        button_width = int(self.screen_width * 0.25)
        button_height = int(self.screen_height * 0.1)
        self.draw_button("Blackjack", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.4), button_width, button_height)
        self.draw_button("Texas Hold'em", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.55), button_width, button_height)
        self.draw_button("Blackjack Tutorial", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.7), button_width, button_height)

    def draw_button(self, text: str, x: int, y: int, width: int, height: int):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if x < mouse[0] < x + width and y < mouse[1] < y + height:
            pygame.draw.rect(self.screen, (70, 130, 180), (x, y, width, height))
            if click[0] == 1:
                return text.lower()
        else:
            pygame.draw.rect(self.screen, (100, 100, 100), (x, y, width, height))

        text_surface = self.small_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text_surface, text_rect)
        return None

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.update_sizes()

            self.draw()

            # Check for button clicks
            selected_game = None
            button_width = int(self.screen_width * 0.25)
            button_height = int(self.screen_height * 0.1)
            if selected_game := self.draw_button("Blackjack", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.4), button_width, button_height):
                game = BlackjackGame(self.screen)
                result = game.run()
                if result == 'quit':
                    pygame.quit()
                    sys.exit()
                    elif selected_game := self.draw_button("Texas Hold'em", self.screen_width // 2 - button_width // 2,int(self.screen_height * 0.55), button_width, button_height):
                    game = TexasHoldemGame(self.screen)
                    result = game.run()
                    if result == 'quit':
                        pygame.quit()
                        sys.exit()
            elif selected_game := self.draw_button("Blackjack Tutorial", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.7), button_width, button_height):
                tutorial = BlackjackTutorial(self.screen)
                result = tutorial.run()
                if result == 'quit':
                    pygame.quit()
                    sys.exit()

            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    menu = MainMenu()
    menu.run()