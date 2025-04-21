# --- START OF FILE TexasHoldemTutorial.py ---

import pygame
import os # Needed for path joining

# *** Import the REAL Card class from blackjack.py ***
try:
    # This assumes blackjack.py is in the same directory
    from blackjack import Card

    # Define card size ratios based on blackjack.py's Card class logic
    # These values MUST match the ones used inside blackjack.Card.load_image
    # Default values from your blackjack.py:
    CARD_WIDTH_RATIO = 0.1
    CARD_HEIGHT_RATIO = 0.2

except ImportError:
    print("FATAL ERROR: Could not import Card from blackjack.py.")
    print("Make sure blackjack.py is in the same directory.")
    pygame.quit()
    exit()
except Exception as e:
    # Handle potential errors if Card definition changes or ratios aren't accessible
    print(f"Warning: Could not determine Card ratios from blackjack.py ({e}). Using defaults.")
    CARD_WIDTH_RATIO = 0.1  # Fallback default
    CARD_HEIGHT_RATIO = 0.2 # Fallback default


# Constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREEN = (0, 80, 0) # A nice background color
FPS = 60
# Use minimum dimensions similar to Blackjack for consistency?
MIN_WIDTH = 800
MIN_HEIGHT = 600
INITIAL_WIDTH = 1000 # Start a bit larger maybe
INITIAL_HEIGHT = 750


class TexasHoldemTutorial:
    # Minimum pixel dimensions for cards, used in load_card_back fallback
    MIN_CARD_WIDTH = 40
    MIN_CARD_HEIGHT = 60

    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        # Ensure minimum dimensions on init
        self.screen_width = max(MIN_WIDTH, self.screen_width)
        self.screen_height = max(MIN_HEIGHT, self.screen_height)
        # Adjust screen if initial size was below minimum
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        self.update_sizes() # Initialize fonts and base sizes FIRST
        self.running = True
        self.clock = pygame.time.Clock()

        # --- Load example cards for visuals using imported Card class ---
        self.example_cards = {} # Initialize empty
        try:
            # Use the imported Card class from blackjack.py
            # !!! IMPORTANT: Constructor order is Card(suit, rank, width, height) !!!
            self.example_cards = {
                "2h": Card("hearts", "2", self.screen_width, self.screen_height),
                "10d": Card("diamonds", "10", self.screen_width, self.screen_height),
                "Jc": Card("clubs", "jack", self.screen_width, self.screen_height),
                "Qs": Card("spades", "queen", self.screen_width, self.screen_height),
                "Kh": Card("hearts", "king", self.screen_width, self.screen_height),
                "As": Card("spades", "ace", self.screen_width, self.screen_height),
                "back": None # Will be initialized in load_card_back()
            }
            print("Example cards loaded successfully.")
        except TypeError as e:
             print(f"FATAL ERROR: TypeError during Card initialization: {e}")
             print("--> Check if Card class constructor in blackjack.py takes exactly (suit, rank, width, height).")
             self.running = False
             return
        except FileNotFoundError as e:
             print(f"FATAL ERROR: FileNotFoundError during Card initialization: {e}")
             print(f"--> Could not find card image file: {e.filename}")
             print(f"--> Ensure 'cards' folder exists and contains '{e.filename.split('/')[-1]}' (or similar).")
             self.running = False
             return
        except Exception as e:
            print(f"FATAL: Failed to initialize example cards: {e}")
            import traceback
            traceback.print_exc() # Print full error details
            self.running = False # Stop if cards can't be made
            return # Stop __init__

        # --- Load the Card Back ---
        # This needs to be called AFTER update_sizes and AFTER example_cards dict exists
        self.load_card_back()

        # --- Tutorial Content Definition ---
        # Using the structure you provided
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
                     # Example visuals for rankings
                     {"card": "As", "x": 0.6, "y": 0.25, "label": "Royal/Str Flush"},
                     {"card": "Kh", "x": 0.8, "y": 0.25, "label": "High Cards"},
                     {"card": "Jc", "x": 0.6, "y": 0.50, "label": "Four of a Kind?"},
                     {"card": "Qs", "x": 0.8, "y": 0.50, "label": "Full House?"},
                     {"card": "10d", "x": 0.6, "y": 0.75, "label": "Flush? Straight?"}
                     # Add more visuals here if desired (e.g., specific hand examples)
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
                    # Visuals showing progression
                    {"card": "Jc", "x": 0.65, "y": 0.3, "label": "Pre-Flop"}, # Hole cards
                    {"card": "Qs", "x": 0.80, "y": 0.3, "label": "Pre-Flop"},
                    {"card": "2h", "x": 0.25, "y": 0.65, "label": "Flop"},     # Flop cards
                    {"card": "10d", "x": 0.40, "y": 0.65, "label": "Flop"},
                    {"card": "Kh", "x": 0.55, "y": 0.65, "label": "Flop"},
                    {"card": "As", "x": 0.70, "y": 0.65, "label": "Turn"},      # Turn card
                    {"card": "back", "x": 0.85, "y": 0.65, "label": "River"}    # River card (shown as back initially)
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
                    # Example strong vs weak hands
                    {"card": "As", "x": 0.6, "y": 0.30, "label": "Strong"},
                    {"card": "Kh", "x": 0.8, "y": 0.30, "label": "Strong"},
                    {"card": "2h", "x": 0.6, "y": 0.65, "label": "Weak"},
                    # Maybe use a different weak card, e.g., 7-2 offsuit if available
                    # Or keep 10d as medium
                    {"card": "10d", "x": 0.8, "y": 0.65, "label": "Medium?"}
                ]
            }
        ]
        self.current_page_index = 0 # Track current page
        # --- Calculate initial positions for visuals ---
        self.reposition_visuals(self.current_page_index)
        print("Tutorial initialized.")


    def load_card_back(self):
        """Loads and scales the card_back.jpg image."""
        # Calculate size using the SAME ratios as blackjack.py's Card class
        # Use max() with MIN_CARD_WIDTH/HEIGHT to prevent tiny cards on small screens
        card_width = max(self.MIN_CARD_WIDTH, int(self.screen_width * CARD_WIDTH_RATIO))
        card_height = max(self.MIN_CARD_HEIGHT, int(self.screen_height * CARD_HEIGHT_RATIO))
        try:
            # Construct path relative to the script
            script_dir = os.path.dirname(__file__) # Get directory where this script is
            img_path = os.path.join(script_dir, "cards", "card_back.jpg") # LOAD THE JPG
            # print(f"Loading card back from: {img_path}") # Debug print
            back_image = pygame.image.load(img_path).convert() # Use convert() for JPG (no alpha)
            self.example_cards["back"] = pygame.transform.smoothscale(back_image, (card_width, card_height))
            # print("Card back loaded and scaled.")
        except (pygame.error, FileNotFoundError) as e:
            print(f"ERROR loading card back image '{img_path}': {e}")
            print("--> Using placeholder blue surface instead.")
            # Create a fallback blue surface if image loading fails
            fallback_surface = pygame.Surface((card_width, card_height))
            fallback_surface.fill((70, 70, 255)) # Blue back color
            pygame.draw.rect(fallback_surface, BLACK, fallback_surface.get_rect(), 2) # Black border
            self.example_cards["back"] = fallback_surface
        except Exception as e:
             print(f"Unexpected error loading card back: {e}")
             # Still provide a fallback
             fallback_surface = pygame.Surface((card_width, card_height))
             fallback_surface.fill((255, 0, 0)) # Red error color
             self.example_cards["back"] = fallback_surface


    def update_sizes(self):
        """Updates screen dimensions, fonts, and resizes cards upon window resize."""
        # Update screen dimensions state, ensuring minimums
        current_w, current_h = self.screen.get_size()
        self.screen_width = max(MIN_WIDTH, current_w)
        self.screen_height = max(MIN_HEIGHT, current_h)

        # Recreate fonts based on the new height for scalability
        try:
            self.font_large = pygame.font.SysFont('Arial', int(self.screen_height * 0.08))
            self.font_medium = pygame.font.SysFont('Arial', int(self.screen_height * 0.05))
            self.font_small = pygame.font.SysFont('Arial', int(self.screen_height * 0.04))
            self.font_label = pygame.font.SysFont('Arial', int(self.screen_height * 0.03)) # Font for card labels
        except Exception as e:
            print(f"Error initializing fonts: {e}. Using default fonts.")
            self.font_large = pygame.font.Font(None, 48) # Fallback default size
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
            self.font_label = pygame.font.Font(None, 20)


        # Update size of all example FACE cards using their own update_size method
        # This delegates the resizing logic (including image reloading/scaling)
        # to the Card class from blackjack.py
        if hasattr(self, 'example_cards'): # Ensure dict exists before iterating
            for card_key, card_obj in self.example_cards.items():
                if card_key != "back" and card_obj and hasattr(card_obj, 'update_size'):
                    try:
                        card_obj.update_size(self.screen_width, self.screen_height)
                    except Exception as e:
                        print(f"Error updating size for card '{card_key}': {e}")

            # Reload/resize the card BACK separately using our consistent logic
            self.load_card_back()
        # print("Sizes updated.")


    def reposition_visuals(self, page_index):
        """Calculates and stores absolute pixel positions for visuals on the current page."""
        if not (hasattr(self, 'pages') and 0 <= page_index < len(self.pages)):
             print(f"Error: Invalid page index {page_index} or pages not initialized.")
             return # Invalid index or pages not ready

        page = self.pages[page_index]

        if "visuals" in page:
            for visual in page["visuals"]:
                # Calculate absolute pixel coordinates from relative (0.0-1.0) coords
                try:
                    x_pos = int(visual["x"] * self.screen_width)
                    y_pos = int(visual["y"] * self.screen_height)

                    # Store these calculated positions *in the visual dictionary itself*
                    # This avoids recalculating them every frame in draw_page
                    visual["abs_x"] = x_pos
                    visual["abs_y"] = y_pos
                except KeyError as e:
                    print(f"Error: Visual definition missing key {e} in page {page_index}.")
                except Exception as e:
                    print(f"Error calculating position for visual {visual.get('card', 'N/A')}: {e}")

        # print(f"Visuals repositioned for page {page_index}.")


    def draw_page(self, page_index):
        """Draws all elements (title, text, visuals) for the specified page index."""
        if not (hasattr(self, 'pages') and 0 <= page_index < len(self.pages)):
             # Don't draw if pages aren't ready or index is invalid
             self.screen.fill(BLACK)
             err_font = pygame.font.Font(None, 30)
             err_surf = err_font.render("Error loading tutorial page.", True, WHITE)
             err_rect = err_surf.get_rect(center=(self.screen_width//2, self.screen_height//2))
             self.screen.blit(err_surf, err_rect)
             return

        page = self.pages[page_index]

        # --- Background ---
        self.screen.fill(DARK_GREEN) # Use the dark green background

        # --- Draw Title ---
        if hasattr(self, 'font_large'):
            try:
                title = self.font_large.render(page.get("title", "No Title"), True, WHITE)
                title_rect = title.get_rect(center=(self.screen_width // 2, int(self.screen_height * 0.07)))
                self.screen.blit(title, title_rect)
            except Exception as e:
                print(f"Error drawing title: {e}")
        else: print("Warning: font_large not initialized.")


        # --- Draw Text Block (Left Side) ---
        if hasattr(self, 'font_medium') and hasattr(self, 'font_small'):
            text_x = int(self.screen_width * 0.05)
            text_y_start = int(self.screen_height * 0.18)
            line_height_large = int(self.screen_height * 0.06)
            line_height_small = int(self.screen_height * 0.045)

            y_pos = text_y_start
            for line in page.get("text", ["Error: Text missing."]):
                try:
                    is_bullet = line.strip().startswith("-")
                    if is_bullet:
                        render_font = self.font_small
                        render_line = "  " + line.strip() # Add indentation for bullets
                        line_spacing = line_height_small
                    elif line == "": # Handle deliberate empty lines for spacing
                        render_font = None # Don't render anything
                        line_spacing = line_height_small * 0.5 # Smaller gap for empty line
                    else:
                        render_font = self.font_medium
                        render_line = line
                        line_spacing = line_height_large

                    if render_font: # Only render if we have a font and text
                        text_surface = render_font.render(render_line, True, WHITE)
                        self.screen.blit(text_surface, (text_x, y_pos))

                    y_pos += line_spacing # Move down for the next line
                except Exception as e:
                    print(f"Error rendering text line '{line}': {e}")
                    y_pos += line_height_small # Skip line on error but advance position
        else: print("Warning: text fonts not initialized.")


        # --- Draw Visuals Block (Right Side) ---
        if "visuals" in page and hasattr(self, 'example_cards') and hasattr(self, 'font_label'):
            for visual in page["visuals"]:
                try:
                    # Use pre-calculated absolute positions stored in the dictionary
                    x_pos = visual.get("abs_x", int(self.screen_width * 0.7)) # Fallback X
                    y_pos = visual.get("abs_y", int(self.screen_height * 0.5)) # Fallback Y

                    card_key = visual.get("card")
                    if not card_key: continue # Skip if no card key

                    # Get the Card object or the back Surface from our dictionary
                    image_to_draw = self.example_cards.get(card_key)

                    img_height = self.MIN_CARD_HEIGHT # Default height for label positioning
                    img_width = self.MIN_CARD_WIDTH   # Default width

                    if image_to_draw:
                        # Check if it's a Card object (from blackjack.py)
                        if isinstance(image_to_draw, Card):
                            if image_to_draw.image: # Make sure Card has loaded its image
                                img_surface = image_to_draw.image
                                img_height = img_surface.get_height()
                                img_width = img_surface.get_width()
                                # *** Set the Card's internal x, y for its draw method ***
                                image_to_draw.x = x_pos
                                image_to_draw.y = y_pos
                                image_to_draw.draw(self.screen) # Use Card's own draw method
                            else:
                                # Card object exists but image failed? Draw placeholder.
                                print(f"Warning: Card '{card_key}' image attribute is None.")
                                pygame.draw.rect(self.screen, (255, 0, 0), (x_pos, y_pos, img_width, img_height), 2)

                        # Check if it's the card back (which is a pygame.Surface)
                        elif isinstance(image_to_draw, pygame.Surface):
                            img_surface = image_to_draw
                            img_height = img_surface.get_height()
                            img_width = img_surface.get_width()
                            self.screen.blit(img_surface, (x_pos, y_pos)) # Draw the Surface directly

                        else: # Should not happen if init is correct
                             print(f"Warning: Visual '{card_key}' is neither Card nor Surface.")
                             pygame.draw.rect(self.screen, (255, 0, 0), (x_pos, y_pos, img_width, img_height))

                    else:
                        # Card key specified in 'visuals' but not found in 'example_cards'
                        print(f"Warning: Card key '{card_key}' not found in example_cards.")
                        pygame.draw.rect(self.screen, (255, 0, 0), (x_pos, y_pos, img_width, img_height))


                    # --- Draw the Label ---
                    label_text = visual.get("label", "") # Get label text, default to empty
                    if label_text: # Only draw if there's a label
                         label_surface = self.font_label.render(label_text, True, WHITE)
                         # Position label centered *below* the visual, using its actual drawn width/height
                         label_rect = label_surface.get_rect(
                             center=(x_pos + img_width // 2,            # Center X under the card
                                     y_pos + img_height + int(self.screen_height * 0.02)) # Y below card + small gap
                         )
                         self.screen.blit(label_surface, label_rect)

                except Exception as e:
                     print(f"Error drawing visual '{visual.get('card', 'N/A')}': {e}")
                     import traceback
                     traceback.print_exc() # More details on error

        elif not hasattr(self, 'example_cards'): print("Warning: example_cards not initialized.")
        elif not hasattr(self, 'font_label'): print("Warning: font_label not initialized.")


    def run(self):
        """Main loop for the tutorial screen."""
        if not self.running: # Check if initialization failed
            print("Tutorial cannot run due to initialization errors.")
            return 'menu' # Or 'quit'

        # Ensure initial visuals are positioned correctly *after* all loading
        self.reposition_visuals(self.current_page_index)

        while self.running:
            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return 'quit' # Signal quit application

                elif event.type == pygame.VIDEORESIZE:
                    # User resized the window
                    new_width = max(MIN_WIDTH, event.w)
                    new_height = max(MIN_HEIGHT, event.h)
                    try:
                        self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                        # CRITICAL: Update sizes and reposition everything
                        self.update_sizes()
                        self.reposition_visuals(self.current_page_index)
                    except pygame.error as e:
                         print(f"Error resizing screen: {e}")
                         # Optionally try to revert or handle gracefully

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return 'menu' # Signal return to main menu
                    else:
                        # Any other key advances the page
                        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
                        self.reposition_visuals(self.current_page_index) # Reposition for new page's visuals

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left mouse click advances page
                        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
                        self.reposition_visuals(self.current_page_index) # Reposition for new page

            # --- Drawing ---
            try:
                 self.draw_page(self.current_page_index)
            except Exception as e:
                 print(f"FATAL DRAW ERROR on page {self.current_page_index}: {e}")
                 # Draw an error message on screen to prevent crash loop maybe?
                 self.screen.fill(BLACK)
                 err_font = pygame.font.Font(None, 30)
                 err_surf = err_font.render(f"Error drawing page {self.current_page_index}. Check console.", True, RED)
                 err_rect = err_surf.get_rect(center=(self.screen_width//2, self.screen_height//2))
                 self.screen.blit(err_surf, err_rect)
                 # Consider setting self.running = False here to stop gracefully

            # --- Update Display ---
            pygame.display.flip()

            # --- Frame Rate Control ---
            self.clock.tick(FPS)

        return 'menu' # Default return action


# ======================================================
# Main Execution Block (for testing the tutorial directly)
# ======================================================
if __name__ == "__main__":
    print("Running TexasHoldemTutorial directly for testing...")
    pygame.init()
    pygame.font.init() # Explicitly initialize font module

    # Create the initial screen / window
    screen = None # Initialize screen to None
    try:
        screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Texas Hold'em Tutorial (Test Mode)")

        # Create and run the tutorial instance
        tutorial = TexasHoldemTutorial(screen)

        # Only run if initialization didn't set self.running to False
        if tutorial.running:
            result = tutorial.run() # Start the tutorial loop
            print(f"Tutorial finished with result: {result}")
        else:
            print("Tutorial initialization failed. Cannot run.")
            # Keep window open for a bit to see console errors
            pygame.time.wait(5000)


    except pygame.error as e:
        print(f"\n--- Pygame Error ---")
        print(e)
        print("Ensure Pygame is installed ('pip install pygame').")
        print("Ensure display drivers are working.")
    except ImportError as e:
         print(f"\n--- Import Error ---")
         print(e)
         print("Make sure 'blackjack.py' is in the same directory as this script.")
    except FileNotFoundError as e:
         print(f"\n--- File Not Found Error ---")
         print(e)
         print("Could not find required image file.")
         print("Ensure the 'cards' folder exists in the same directory.")
         print("Ensure required card images (e.g., 'ace_of_spades.jpg', 'card_back.jpg') are inside 'cards/'.")
    except Exception as e:
         print(f"\n--- An Unexpected Error Occurred ---")
         import traceback
         traceback.print_exc() # Print detailed traceback for unexpected errors
    finally:
        print("Quitting Pygame.")
        pygame.quit() # Cleanly exit Pygame

