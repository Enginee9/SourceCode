# --- START OF FILE TexasHoldemTutorial.py ---

import pygame
import os # Needed for path joining

# *** Import the REAL Card class from blackjack.py ***
try:
    from blackjack import Card
    # Get the sizing ratios from the blackjack Card class if possible
    # Note: This assumes blackjack.py defines Card at the top level.
    # If Card is defined elsewhere, this might need adjustment.
    # We'll define defaults here and let the Card class handle its own sizing.
    CARD_WIDTH_RATIO = 0.1  # Match blackjack.py Card's internal ratio
    CARD_HEIGHT_RATIO = 0.2 # Match blackjack.py Card's internal ratio
except ImportError:
    print("FATAL ERROR: Could not import Card from blackjack.py.")
    print("Make sure blackjack.py is in the same directory.")
    pygame.quit()
    exit()
except Exception as e:
    print(f"Error during import or accessing Card ratios: {e}")
    # Define fallback ratios if needed, though Card class should handle it
    CARD_WIDTH_RATIO = 0.08
    CARD_HEIGHT_RATIO = 0.18


# Constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FPS = 60
MIN_WIDTH = 400  # Minimum window width (Blackjack uses 800, maybe increase this?)
MIN_HEIGHT = 300 # Minimum window height (Blackjack uses 600, maybe increase this?)
INITIAL_WIDTH = 1000 # Keep initial size flexible
INITIAL_HEIGHT = 700


class TexasHoldemTutorial:
    # Remove internal Card dimension constants, rely on imported Card's sizing
    # DEFAULT_CARD_WIDTH_RATIO = 0.0625 # Removed
    # DEFAULT_CARD_HEIGHT_RATIO = 0.1667 # Removed
    MIN_CARD_WIDTH = 40 # Keep minimum pixel sizes maybe? Or remove if Card handles it.
    MIN_CARD_HEIGHT = 60 # Keep minimum pixel sizes maybe? Or remove if Card handles it.

    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        # Ensure minimum dimensions on init
        self.screen_width = max(MIN_WIDTH, self.screen_width)
        self.screen_height = max(MIN_HEIGHT, self.screen_height)
        # Resizing the screen might be necessary if initial size < MIN_WIDTH/MIN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        self.update_sizes() # Initialize fonts etc. FIRST
        self.running = True
        self.clock = pygame.time.Clock()

        # Load example cards for visuals using imported Card class
        self.example_cards = {} # Initialize empty
        try:
            # Use the imported Card class - NOTE THE SUIT, RANK ORDER!
            self.example_cards = {
                "2h": Card("hearts", "2", self.screen_width, self.screen_height),
                "10d": Card("diamonds", "10", self.screen_width, self.screen_height),
                "Jc": Card("clubs", "jack", self.screen_width, self.screen_height),
                "Qs": Card("spades", "queen", self.screen_width, self.screen_height),
                "Kh": Card("hearts", "king", self.screen_width, self.screen_height),
                "As": Card("spades", "ace", self.screen_width, self.screen_height),
                "back": None # Will be initialized in load_card_back()
            }
        except TypeError as e:
             print(f"FATAL ERROR: TypeError during Card initialization: {e}")
             print("Check if Card class constructor in blackjack.py matches (suit, rank, width, height).")
             self.running = False
             return
        except Exception as e:
            print(f"FATAL: Failed to initialize example cards: {e}")
            self.running = False # Stop if cards can't be made
            return # Stop __init__

        self.load_card_back() # Load after update_sizes and card init attempt

        # Tutorial content with visuals (Adjust relative coords if needed due to card size)
        # Note: Blackjack cards are larger (0.1w, 0.2h) vs previous (0.0625w, 0.1667h)
        # You might need to space visuals out more (adjust 'x' and 'y' values)
        self.pages = [
             {
                "title": "TEXAS HOLD'EM BASICS",
                "text": [
                    "Objective: Make the best 5-card hand",
                    "using any combination of your 2 hole",
                    "cards and the 5 community cards.",
                    "",
                    "Game Flow:",
                    "- Each player gets 2 private cards ('hole cards')",
                    "- 5 community cards dealt face up (Flop, Turn, River)",
                    "- Betting rounds occur before/after deals",
                    "- Showdown: Remaining players reveal hands"
                ],
                 "visuals": [
                    # Adjusted coords slightly for potentially larger cards
                    {"card": "Jc", "x": 0.65, "y": 0.30, "label": "Hole Card"},
                    {"card": "Qs", "x": 0.80, "y": 0.30, "label": "Hole Card"},
                    {"card": "back", "x": 0.65, "y": 0.65, "label": "Card Back"},
                    {"card": "back", "x": 0.80, "y": 0.65, "label": "Card Back"},
                    {"card": "2h", "x": 0.05, "y": 0.65, "label": "Community"},
                    {"card": "10d", "x": 0.20, "y": 0.65, "label": "Community"},
                    {"card": "Kh", "x": 0.35, "y": 0.65, "label": "Community"}
                ]
            },
            {
                "title": "HAND RANKINGS",
                "text": [
                    "Strongest to Weakest:",
                    "- Royal Flush (A-K-Q-J-10, same suit)",
                    "- Straight Flush (5 sequential, same suit)",
                    "- Four of a Kind (e.g., four 7s)",
                    "- Full House (Three of a kind + Pair)",
                    "- Flush (5 cards, same suit, not sequential)",
                    "- Straight (5 sequential, different suits)",
                    "- Three of a Kind (e.g., three Jacks)",
                    "- Two Pair (e.g., two Aces and two 8s)",
                    "- One Pair (e.g., two Kings)",
                    "- High Card (Highest card plays if no pair+)"
                ],
                "visuals": [
                     {"card": "As", "x": 0.6, "y": 0.25, "label": "Royal/Str Flush"},
                     {"card": "Kh", "x": 0.8, "y": 0.25, "label": "High Cards"},
                     {"card": "Jc", "x": 0.6, "y": 0.50, "label": "Four of a Kind?"},
                     {"card": "Qs", "x": 0.8, "y": 0.50, "label": "Full House?"},
                     {"card": "10d", "x": 0.6, "y": 0.75, "label": "Flush? Straight?"}
                ]
            },
            {
                "title": "BETTING ROUNDS",
                "text": [
                    "1. Pre-Flop: After hole cards dealt.",
                    "   (Players see only their 2 cards)",
                    "2. Flop: After first 3 community cards.",
                    "   (Players see 2 hole + 3 community)",
                    "3. Turn: After 4th community card.",
                    "   (Players see 2 hole + 4 community)",
                    "4. River: After 5th (final) community card.",
                    "   (Players see 2 hole + 5 community)",
                    "",
                    "Actions: Check, Bet, Call, Raise, Fold"
                ],
                "visuals": [
                    {"card": "Jc", "x": 0.65, "y": 0.3, "label": "Pre-Flop"},
                    {"card": "Qs", "x": 0.80, "y": 0.3, "label": "Pre-Flop"},
                    {"card": "2h", "x": 0.25, "y": 0.65, "label": "Flop"},
                    {"card": "10d", "x": 0.40, "y": 0.65, "label": "Flop"},
                    {"card": "Kh", "x": 0.55, "y": 0.65, "label": "Flop"},
                    {"card": "As", "x": 0.70, "y": 0.65, "label": "Turn"},
                    {"card": "back", "x": 0.85, "y": 0.65, "label": "River"}
                ]
            },
            {
                "title": "GAME STRATEGY (Very Basic)",
                "text": [
                    "Starting Hands: Some 2-card hands",
                    "are much stronger than others (e.g., A-A,",
                    "K-K, A-K suited). Play tight initially.",
                    "",
                    "Position: Acting later is an advantage.",
                    "You see others' actions before deciding.",
                    "",
                    "Observation: Watch betting patterns.",
                    "Bluffing is part of the game.",
                    "",
                    "Bankroll: Never bet more than you",
                    "can afford to lose.",
                    "",
                    "Press Esc to return | Click/Key to advance"
                ],
                "visuals": [
                    {"card": "As", "x": 0.6, "y": 0.30, "label": "Strong"},
                    {"card": "Kh", "x": 0.8, "y": 0.30, "label": "Strong"},
                    {"card": "2h", "x": 0.6, "y": 0.65, "label": "Weak"},
                    {"card": "10d", "x": 0.8, "y": 0.65, "label": "Medium?"}
                ]
            }
        ]
        self.current_page_index = 0 # Track current page
        self.reposition_visuals(self.current_page_index)  # Initialize visual positions

    def load_card_back(self):
        # Calculate size using the SAME ratios as blackjack.py's Card class
        # Use max with MIN_CARD_WIDTH/HEIGHT if you kept them, otherwise remove max()
        card_width = max(self.MIN_CARD_WIDTH, int(self.screen_width * CARD_WIDTH_RATIO))
        card_height = max(self.MIN_CARD_HEIGHT, int(self.screen_height * CARD_HEIGHT_RATIO))
        try:
            # Construct path relative to the script
            script_dir = os.path.dirname(__file__) # Get directory of the script
            img_path = os.path.join(script_dir, "cards", "card_back.jpg") # LOAD JPG
            back_image = pygame.image.load(img_path).convert() # Use convert() for JPG
            self.example_cards["back"] = pygame.transform.smoothscale(back_image, (card_width, card_height))
        except (pygame.error, FileNotFoundError) as e:
            print(f"Error loading card back image {img_path}: {e}. Using placeholder.")
            # Fallback surface
            self.example_cards["back"] = pygame.Surface((card_width, card_height))
            self.example_cards["back"].fill((70, 70, 255)) # Blue back
            pygame.draw.rect(self.example_cards["back"], BLACK, (0, 0, card_width, card_height), 2)

    def update_sizes(self):
        # Update screen dimensions, ensuring minimums
        current_w, current_h = self.screen.get_size()
        self.screen_width = max(MIN_WIDTH, current_w)
        self.screen_height = max(MIN_HEIGHT, current_h)
        # Recreate fonts based on new height
        self.font_large = pygame.font.SysFont('Arial', int(self.screen_height * 0.08))
        self.font_medium = pygame.font.SysFont('Arial', int(self.screen_height * 0.05))
        self.font_small = pygame.font.SysFont('Arial', int(self.screen_height * 0.04))
        self.font_label = pygame.font.SysFont('Arial', int(self.screen_height * 0.03)) # Smaller label font

        # Update size of all example FACE cards using their own update_size
        for card_key, card_obj in self.example_cards.items():
            if card_key != "back" and card_obj: # Check if card object exists and isn't back
                # Calling card_obj.update_size will use the logic from blackjack.Card
                card_obj.update_size(self.screen_width, self.screen_height)

        # Reload/resize the card BACK separately using our consistent logic
        self.load_card_back()


    def reposition_visuals(self, page_index):
        """Reposition visuals for the current page based on screen size."""
        if not 0 <= page_index < len(self.pages):
             return # Invalid index
        page = self.pages[page_index]

        if "visuals" in page:
            for visual in page["visuals"]:
                # Calculate absolute pixel coordinates from relative (0.0-1.0) coords
                x_pos = int(visual["x"] * self.screen_width)
                y_pos = int(visual["y"] * self.screen_height)

                # Store these calculated positions in the visual dict for drawing
                visual["abs_x"] = x_pos
                visual["abs_y"] = y_pos

                # We don't need to update card.x/y here anymore,
                # because draw_page will set them just before drawing.


    def draw_page(self, page_index):
        if not 0 <= page_index < len(self.pages):
             return # Invalid index
        page = self.pages[page_index]

        self.screen.fill((0, 80, 0)) # Dark Green background

        # --- Draw Title ---
        title = self.font_large.render(page["title"], True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, int(self.screen_height * 0.07)))
        self.screen.blit(title, title_rect)

        # --- Draw Text (Left Side) ---
        text_x = int(self.screen_width * 0.05)
        text_y_start = int(self.screen_height * 0.18)
        line_height_large = int(self.screen_height * 0.06)
        line_height_small = int(self.screen_height * 0.045)

        y_pos = text_y_start
        for line in page["text"]:
            is_bullet = line.strip().startswith("-")
            if is_bullet:
                render_font = self.font_small
                render_line = "  " + line.strip()
                line_spacing = line_height_small
            elif line == "":
                render_font = None
                line_spacing = line_height_small * 0.5
            else:
                render_font = self.font_medium
                render_line = line
                line_spacing = line_height_large

            if render_font:
                text_surface = render_font.render(render_line, True, WHITE)
                self.screen.blit(text_surface, (text_x, y_pos))

            y_pos += line_spacing


        # --- Draw Visuals (Right Side) ---
        if "visuals" in page:
            for visual in page["visuals"]:
                x_pos = visual.get("abs_x", int(visual["x"] * self.screen_width))
                y_pos = visual.get("abs_y", int(visual["y"] * self.screen_height))

                card_key = visual["card"]
                image_to_draw = self.example_cards.get(card_key) # Gets Card object or Surface

                if image_to_draw:
                    # Get current actual dimensions of the image/card surface
                    if hasattr(image_to_draw, 'image') and image_to_draw.image: # It's a Card object
                        img_surface = image_to_draw.image
                        img_height = img_surface.get_height()
                        img_width = img_surface.get_width()
                         # *** FIX for draw() method ***
                        image_to_draw.x = x_pos # Set card's internal x
                        image_to_draw.y = y_pos # Set card's internal y
                        image_to_draw.draw(self.screen) # Call blackjack.Card's draw()
                    elif isinstance(image_to_draw, pygame.Surface): # It's the card back Surface
                        img_surface = image_to_draw
                        img_height = img_surface.get_height()
                        img_width = img_surface.get_width()
                        self.screen.blit(img_surface, (x_pos, y_pos)) # Draw the back surface directly
                    else: # Fallback / Error case
                         print(f"Warning: Visual '{card_key}' is not a Card or Surface.")
                         img_height = 70
                         img_width = 50
                         pygame.draw.rect(self.screen, (255,0,0), (x_pos, y_pos, img_width, img_height))

                else:
                    print(f"Warning: Card key '{card_key}' not found in example_cards for drawing.")
                    img_height = 70 # Placeholder dimensions
                    img_width = 50
                    pygame.draw.rect(self.screen, (255,0,0), (x_pos, y_pos, img_width, img_height))


                # Draw the label BELOW the card/visual, centered horizontally
                label_text = visual.get("label", "")
                if label_text and hasattr(self, 'font_label'): # Check font exists
                     label_surface = self.font_label.render(label_text, True, WHITE)
                     # Position label centered below the visual, using actual image height
                     label_rect = label_surface.get_rect(center=(x_pos + img_width // 2, y_pos + img_height + int(self.screen_height * 0.02))) # Adjust vertical offset
                     self.screen.blit(label_surface, label_rect)


    def run(self):
        self.current_page_index = 0
        # Ensure initial visuals are positioned AFTER cards are loaded & sized
        self.reposition_visuals(self.current_page_index)

        while self.running:
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit' # Signal quit
                elif event.type == pygame.VIDEORESIZE:
                    new_width = max(MIN_WIDTH, event.w)
                    new_height = max(MIN_HEIGHT, event.h)
                    self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                    self.update_sizes() # Updates fonts, card sizes (incl. back)
                    self.reposition_visuals(self.current_page_index) # Reposition for new size
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'menu' # Signal return to menu
                    else:
                        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
                        self.reposition_visuals(self.current_page_index) # Reposition for new page
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
                        self.reposition_visuals(self.current_page_index) # Reposition for new page

            # Drawing
            self.draw_page(self.current_page_index)

            # Update Display
            pygame.display.flip()

            # Frame Rate Control
            self.clock.tick(FPS)

        return 'menu' # Default return if loop exits unexpectedly


# ======================================================
# Main Execution Block
# ======================================================
if __name__ == "__main__":
    pygame.init()
    pygame.font.init() # Explicitly initialize font module

    # Create the initial screen / window
    try:
        screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Texas Hold'em Tutorial")

        # Create and run the tutorial instance
        tutorial = TexasHoldemTutorial(screen)
        if tutorial.running: # Check if init failed
            result = tutorial.run() # Start the tutorial loop
            print(f"Tutorial finished with result: {result}")
        else:
            print("Tutorial initialization failed. Exiting.")

    except pygame.error as e:
        print(f"\nPygame Error: {e}")
        print("Ensure Pygame is installed correctly ('pip install pygame')")
        print("Ensure any required image files (e.g., in 'cards/') exist and are accessible.")
        print("Filenames should be like 'king_of_spades.jpg', 'card_back.jpg'.")
    except Exception as e:
         print(f"\nAn unexpected error occurred in the main block: {e}")
         import traceback
         traceback.print_exc() # Print detailed traceback
    finally:
        pygame.quit() # Cleanly exit Pygame

# --- END OF FILE TexasHoldemTutorial.py ---