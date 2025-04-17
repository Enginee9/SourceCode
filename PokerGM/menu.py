import pygame
import sys
import time
from blackjack import BlackjackGame
from tutorial import BlackjackTutorial
from texas_holdem import TexasHoldemGame
from TexasHoldemTutorial import TexasHoldemTutorial

# Constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
DARK_RED = (150, 0, 0)
GRAY = (200, 200, 200)


class MainMenu:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        pygame.display.set_caption("Devil's Gamble")
        self.clock = pygame.time.Clock()
        self.font = None
        self.small_font = None
        self.screen_width, self.screen_height = self.screen.get_size()
        self.update_sizes()

        # Show the cinematic intro immediately
        self.show_devil_intro()

    def update_sizes(self):
        """Update fonts and sizes when window is resized"""
        self.screen_width, self.screen_height = self.screen.get_size()
        try:
            self.font = pygame.font.SysFont('Arial', min(72, int(self.screen_height * 0.1)))
            self.small_font = pygame.font.SysFont('Arial', min(24, int(self.screen_height * 0.04)))
        except:
            self.font = pygame.font.Font(None, 72)
            self.small_font = pygame.font.Font(None, 24)

    def show_devil_intro(self):
        """Show the full cinematic intro with proper event handling"""
        self.screen.fill(BLACK)
        pygame.display.flip()

        # Font setup
        try:
            title_font = pygame.font.SysFont('Arial', min(72, int(self.screen_height * 0.1)), bold=True)
            main_font = pygame.font.SysFont('Arial', min(24, int(self.screen_height * 0.04)))
        except:
            title_font = pygame.font.Font(None, 72)
            main_font = pygame.font.Font(None, 24)

        # Display settings
        margin = int(self.screen_width * 0.1)
        line_height = main_font.get_height() + 5
        max_lines = (self.screen_height - 2 * margin) // line_height
        all_lines = []
        scroll_pos = 0

        def render_wrapped(text, font, color=WHITE):
            """Render text with word wrapping"""
            words = text.split(' ')
            lines = []
            current_line = words[0]

            for word in words[1:]:
                test_line = f"{current_line} {word}"
                if font.size(test_line)[0] <= (self.screen_width - 2 * margin):
                    current_line = test_line
                else:
                    lines.append((current_line, color))
                    current_line = word
            lines.append((current_line, color))
            return lines

        def add_lines(text, color=WHITE, delay=1.0):
            """Add new lines to the scene with proper event handling"""
            nonlocal all_lines, scroll_pos

            if text == "":
                all_lines.append(("", color))
            else:
                wrapped = render_wrapped(text, main_font, color)
                all_lines.extend(wrapped)

            # Auto-scroll if needed
            if len(all_lines) > max_lines:
                scroll_pos = len(all_lines) - max_lines

            redraw_screen()

            # Handle events during delay
            start_time = time.time()
            while time.time() - start_time < delay:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        return False  # Skip remaining scenes
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        return False  # Skip remaining scenes
                pygame.time.delay(10)

            return True

        def redraw_screen():
            """Redraw all visible text"""
            self.screen.fill(BLACK)

            # Determine which lines to show
            start_idx = max(0, scroll_pos)
            end_idx = min(start_idx + max_lines, len(all_lines))
            visible_lines = all_lines[start_idx:end_idx]

            # Draw visible lines
            y_pos = margin
            for line, color in visible_lines:
                if line:  # Skip empty lines
                    text_surface = main_font.render(line, True, color)
                    self.screen.blit(text_surface, (margin, y_pos))
                y_pos += line_height

            pygame.display.flip()

        # Show title screen
        title = title_font.render("DEVIL'S BLACKJACK", True, RED)
        subtitle = main_font.render("Do you dare to play?", True, WHITE)

        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, self.screen_height // 3))
        self.screen.blit(subtitle, (self.screen_width // 2 - subtitle.get_width() // 2,
                                    self.screen_height // 3 + title.get_height() + 20))
        pygame.display.flip()

        # Handle events during title screen delay
        start_time = time.time()
        while time.time() - start_time < 2.5:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    break
            pygame.time.delay(10)

        # Start the story


        # Story scenes
        scenes = [
            {"text": "Late night, a rundown underground casino, thick with smoke.", "delay": 2.0},
            {"text": "A man loses his last chips and is thrown out by security.", "delay": 2.5},
            {"text": "", "delay": 0.5},
            {"text": "Man: 'Damn it! One more round... Just one more and I could've won it all back!'",
             "delay": 2.5, "color": GRAY},
            {"text": "", "delay": 0.5},
            {"text": "A whispering voice: 'Seems like you could use some... luck?'", "delay": 2.0, "color": RED},
            {"text": "", "delay": 1.0},
            {"text": "(The man turns to see the Devil standing under a flickering streetlamp", "delay": 2.0},
            {"text": "his shadow stretching unnaturally long)", "delay": 1.5},
            {"text": "", "delay": 0.5},
            {"text": "Man: 'Who are you?'", "delay": 1.5, "color": GRAY},
            {"text": "", "delay": 0.5},
            {"text": "Devil: 'Someone who can give you what you desire... say, endless wealth?'",
             "delay": 3.0, "color": DARK_RED},
            {"text": "", "delay": 0.5},
            {"text": "(He pulls out an ancient deck of cards, its back engraved with eerie runes)", "delay": 2.5},
            {"text": "", "delay": 0.5},
            {"text": "Devil: 'Let's play a game. Win, and I'll give you", "delay": 2.0, "color": DARK_RED},
            {"text": "more money than you could spend in a lifetime.", "delay": 2.0, "color": DARK_RED},
            {"text": "Lose, and you'll only pay... a small price.'", "delay": 2.0, "color": DARK_RED},
            {"text": "", "delay": 0.5},
            {"text": "Man: 'What price?'", "delay": 1.5, "color": GRAY},
            {"text": "", "delay": 1.0},
            {"text": "Devil: 'Oh, nothing you'd miss...", "delay": 2.0, "color": DARK_RED},
            {"text": "Just something you don't... need.'", "delay": 2.0, "color": DARK_RED},
            {"text": "", "delay": 1.0},
            {"text": "Press SPACE or click to continue...", "delay": 0, "blink": True}
        ]

        # Display all scenes with proper event handling
        for scene in scenes:
            if not add_lines(scene.get("text", ""), scene.get("color", WHITE), scene.get("delay", 1.0)):
                break  # Exit if user interrupted

        # Wait for final input
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            pygame.time.delay(10)

    def draw(self):
        """Draw the main menu"""
        self.screen.fill(BLACK)

        # Title
        title = self.font.render("CARD GAMES", True, WHITE)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, int(self.screen_height * 0.15)))

        # Buttons
        button_width = int(self.screen_width * 0.25)
        button_height = int(self.screen_height * 0.1)

        self.draw_button("Blackjack", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.4),
                         button_width, button_height)
        self.draw_button("Texas Hold'em", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.55),
                         button_width, button_height)
        self.draw_button("Tutorial", self.screen_width // 2 - button_width // 2, int(self.screen_height * 0.7),
                         button_width, button_height)

    def draw_button(self, text, x, y, width, height):
        """Draw an interactive button"""
        mouse_pos = pygame.mouse.get_pos()
        clicked = pygame.mouse.get_pressed()[0]

        # Button hover effect
        if x <= mouse_pos[0] <= x + width and y <= mouse_pos[1] <= y + height:
            pygame.draw.rect(self.screen, (70, 130, 180), (x, y, width, height))
            if clicked:
                return text.lower()
        else:
            pygame.draw.rect(self.screen, (100, 100, 100), (x, y, width, height))

        # Button text
        text_surface = self.small_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text_surface, text_rect)
        return None

    def run(self):
        """Main game loop"""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.update_sizes()

            self.draw()

            # Check button clicks
            button_width = int(self.screen_width * 0.25)
            button_height = int(self.screen_height * 0.1)

            if selected := self.draw_button("Blackjack", self.screen_width // 2 - button_width // 2,
                                            int(self.screen_height * 0.4), button_width, button_height):
                game = BlackjackGame(self.screen)
                result = game.run()
                if result == 'quit':
                    pygame.quit()
                    sys.exit()

            elif selected := self.draw_button("Texas Hold'em", self.screen_width // 2 - button_width // 2,
                                              int(self.screen_height * 0.55), button_width, button_height):
                game = TexasHoldemGame(self.screen)
                result = game.run()
                if result == 'quit':
                    pygame.quit()
                    sys.exit()

            elif selected := self.draw_button("Blackjack Tutorial", self.screen_width // 2 - button_width // 2,
                                              int(self.screen_height * 0.7), button_width, button_height):
                tutorial = BlackjackTutorial(self.screen)
                result = tutorial.run()
                if result == 'quit':
                    pygame.quit()
                    sys.exit()
            elif selected_game := self.draw_button("Texas Hold'Em Tutorial", self.screen_width // 3 + button_width // 6 ,int(self.screen_height * 0.85), button_width, button_height):
                tutorial = TexasHoldemTutorial(self.screen)
                result = tutorial.run()
                if result == 'quit':
                    pygame.quit()
                    sys.exit()

            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    menu = MainMenu()
    menu.run()