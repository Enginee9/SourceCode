# --- START OF FILE TexasHoldemTutorial.py ---

import pygame
import os # Needed for path joining
import traceback # For printing detailed errors

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
DARK_GREEN = (1, 2, 3) # A nice background color (Changed from 1,2,3)
RED = (200, 0, 0) # For error messages
FPS = 60
MIN_WIDTH = 1200 # Increased minimum width for 5-card display
MIN_HEIGHT = 800 # Increased minimum height
INITIAL_WIDTH = 1280 # Default start size
INITIAL_HEIGHT = 800

class TexasHoldemTutorial:
    MIN_CARD_WIDTH = 40
    MIN_CARD_HEIGHT = 60

    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.screen_width = max(MIN_WIDTH, self.screen_width)
        self.screen_height = max(MIN_HEIGHT, self.screen_height)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        # Initialize fonts and sizes first, needed by card loading/fallbacks
        self.update_sizes()

        self.running = True
        self.clock = pygame.time.Clock()

        # --- Load MORE example cards for hand ranking visuals ---
        self.example_cards = {}
        cards_to_load = {
            # Original set needed for non-hand pages
            "2h": ("hearts", "2"), "10d": ("diamonds", "10"), "Jc": ("clubs", "jack"),
            "Qs": ("spades", "queen"), "Kh": ("hearts", "king"), "As": ("spades", "ace"),
            # Added for Hand Rankings
            "Ah": ("hearts", "ace"), "Ac": ("clubs", "ace"), "Ad": ("diamonds", "ace"),
            "Ks": ("spades", "king"), "Kd": ("diamonds", "king"), "Kc": ("clubs", "king"),
            "Qh": ("hearts", "queen"), "Qd": ("diamonds", "queen"), "Qc": ("clubs", "queen"),
            "Jh": ("hearts", "jack"), "Js": ("spades", "jack"), "Jd": ("diamonds", "jack"),
            "10s": ("spades", "10"), "10h": ("hearts", "10"), "10c": ("clubs", "10"),
            "9s": ("spades", "9"), "9h": ("hearts", "9"), "9d": ("diamonds", "9"), "9c": ("clubs", "9"),
            "8s": ("spades", "8"), "8h": ("hearts", "8"), "8d": ("diamonds", "8"), "8c": ("clubs", "8"),
            "7s": ("spades", "7"), "7h": ("hearts", "7"), "7d": ("diamonds", "7"), "7c": ("clubs", "7"),
            "6s": ("spades", "6"), "6h": ("hearts", "6"), "6d": ("diamonds", "6"), "6c": ("clubs", "6"),
            "5s": ("spades", "5"), "5h": ("hearts", "5"), "5d": ("diamonds", "5"), "5c": ("clubs", "5"),
            "4s": ("spades", "4"), "4h": ("hearts", "4"), "4d": ("diamonds", "4"), "4c": ("clubs", "4"),
            "3s": ("spades", "3"), "3h": ("hearts", "3"), "3d": ("diamonds", "3"), "3c": ("clubs", "3"),
            "2s": ("spades", "2"), "2d": ("diamonds", "2"), "2c": ("clubs", "2"),
            "back": None # Placeholder for back
        }

        missing_files = []
        init_successful = True # Flag to track if init succeeds
        try:
            for key, card_data in cards_to_load.items():
                if key == "back":
                    continue # Handle back separately after loop
                if card_data is None: # Should not happen with current dict, but safe check
                    continue

                suit, rank = card_data # Unpack tuple
                try:
                    # Create Card instance (suit, rank, width, height)
                    self.example_cards[key] = Card(suit, rank, self.screen_width, self.screen_height)
                except FileNotFoundError as e:
                    # Track missing files but continue loading others
                    missing_file_name = os.path.basename(e.filename) if hasattr(e, 'filename') else f"{rank}_of_{suit}.jpg"
                    if missing_file_name not in missing_files: # Avoid duplicate warnings
                        missing_files.append(missing_file_name)
                    self.example_cards[key] = None # Mark as None if file missing
                    print(f"Warning: Card image file not found for {key}: {missing_file_name}")
                except Exception as card_load_e:
                     print(f"FATAL ERROR loading card {key}: {card_load_e}")
                     init_successful = False
                     break # Stop loop on critical card load error

            if not init_successful:
                 raise RuntimeError("Critical error during card loading.") # Propagate error

            if missing_files:
                 print("\n--- Some card images were missing! ---")
                 print("The tutorial will show placeholders (Red Rectangles) for:")
                 for fname in sorted(missing_files): # Sort for consistent output
                     print(f"- {fname}")
                 print("Make sure these files exist in the 'cards' folder.")
                 print("----------------------------------------\n")

            print("Example cards dictionary populated (or marked as None if missing).")

        except TypeError as e:
             print(f"FATAL ERROR: TypeError during Card initialization: {e}")
             print("--> Check Card class constructor in blackjack.py: (suit, rank, width, height).")
             init_successful = False
        except RuntimeError as e: # Catch the propagated error
             print(e) # Already printed specific error
             init_successful = False
        except Exception as e:
            print(f"FATAL: Failed during example cards dictionary creation: {e}")
            traceback.print_exc() # Print full error details
            init_successful = False

        # Only proceed if card init was okay so far
        if not init_successful:
             self.running = False
             return # Stop __init__

        # --- Load the Card Back (needs to happen after update_sizes) ---
        self.load_card_back()

        # --- Define Page Content ---

        # Coordinates for 5 cards horizontally centered on hand pages
        card_y = 0.55
        card_x = [0.10, 0.26, 0.42, 0.58, 0.74] # Relative X positions

        page_basics = {
            "title": "TEXAS HOLD'EM BASICS",
            "text": [
                "Objective: Make the best 5-card hand",
                "using your 2 hole cards and the 5",
                "community cards.",
                "",
                "Game Flow:",
                "- 2 private 'hole cards' per player",
                "- 5 community cards (Flop, Turn, River)",
                "- Betting rounds",
                "- Showdown",
                "",
                "Click or Press Key to Continue..."
            ],
             "visuals": [
                {"card": "Jc", "x": 0.65, "y": 0.30, "label": "Hole Card"},
                {"card": "Qs", "x": 0.80, "y": 0.30, "label": "Hole Card"},
                {"card": "back", "x": 0.65, "y": 0.75, "label": "Card Back"},
                {"card": "back", "x": 0.80, "y": 0.75, "label": "Card Back"},
                {"card": "2h", "x": 0.05, "y": 0.75, "label": "Community"},
                {"card": "10d", "x": 0.20, "y": 0.75, "label": "Community"},
                {"card": "Kh", "x": 0.35, "y": 0.75, "label": "Community"}
            ]
        }
        page_rankings_intro = {
            "title": "HAND RANKINGS (Overview)",
            "text": [
                "Strongest to Weakest:",
                "- Royal Flush",
                "- Straight Flush",
                "- Four of a Kind",
                "- Full House",
                "- Flush",
                "- Straight",
                "- Three of a Kind",
                "- Two Pair",
                "- One Pair",
                "- High Card",
                "",
                "Next pages show examples...",
                "Click or Press Key to Continue..."
            ],
            "visuals": [
                 # Use cards available in cards_to_load
                 {"card": "As", "x": 0.6, "y": 0.25, "label": "Strongest Card"},
                 {"card": "Kh", "x": 0.8, "y": 0.25, "label": "Strong Card"},
                 {"card": "7d", "x": 0.6, "y": 0.55, "label": "Medium Card"},
                 {"card": "2c", "x": 0.8, "y": 0.55, "label": "Weakest Card"}
            ]
        }

        # --- Define the Detailed Hand Ranking Pages ---
        # This is the list you provided
        hand_pages = [
            {
                "title": "HAND RANKING: ROYAL FLUSH",
                "text": ["Ace, King, Queen, Jack, 10", "All of the same suit.", "The best possible hand.", "", "Click or Press Key to Continue..."],
                "group_label": "Royal Flush (Spades)",
                "visuals": [
                    {"card": "As", "x": card_x[0], "y": card_y}, {"card": "Ks", "x": card_x[1], "y": card_y},
                    {"card": "Qs", "x": card_x[2], "y": card_y}, {"card": "Js", "x": card_x[3], "y": card_y},
                    {"card": "10s","x": card_x[4], "y": card_y},
                ]
            },
            {
                "title": "HAND RANKING: STRAIGHT FLUSH",
                "text": ["Five cards in sequence,", "All of the same suit.", "(Not A-K-Q-J-10)", "", "Click or Press Key to Continue..."],
                "group_label": "Straight Flush (Hearts)",
                "visuals": [
                    {"card": "9h", "x": card_x[0], "y": card_y}, {"card": "8h", "x": card_x[1], "y": card_y},
                    {"card": "7h", "x": card_x[2], "y": card_y}, {"card": "6h", "x": card_x[3], "y": card_y},
                    {"card": "5h", "x": card_x[4], "y": card_y},
                ]
            },
             {
                "title": "HAND RANKING: FOUR OF A KIND",
                "text": ["Four cards of the same rank,", "plus one other card ('kicker').", "", "Click or Press Key to Continue..."],
                "group_label": "Four of a Kind (Aces)",
                "visuals": [
                    {"card": "As", "x": card_x[0], "y": card_y}, {"card": "Ah", "x": card_x[1], "y": card_y},
                    {"card": "Ad", "x": card_x[2], "y": card_y}, {"card": "Ac", "x": card_x[3], "y": card_y},
                    {"card": "Kh", "x": card_x[4], "y": card_y}, # Kicker
                ]
            },
             {
                "title": "HAND RANKING: FULL HOUSE",
                "text": ["Three cards of one rank,", "and two cards of another rank.", "(Three of a kind + Pair)", "", "Click or Press Key to Continue..."],
                "group_label": "Full House (Kings full of Queens)",
                "visuals": [
                    {"card": "Kh", "x": card_x[0], "y": card_y}, {"card": "Kd", "x": card_x[1], "y": card_y},
                    {"card": "Kc", "x": card_x[2], "y": card_y}, # Three Kings
                    {"card": "Qs", "x": card_x[3], "y": card_y}, {"card": "Qh", "x": card_x[4], "y": card_y}, # Pair of Queens
                ]
            },
             {
                "title": "HAND RANKING: FLUSH",
                "text": ["Five cards of the same suit,", "but not in sequence.", "", "Click or Press Key to Continue..."],
                "group_label": "Flush (Hearts)",
                "visuals": [
                    {"card": "Kh", "x": card_x[0], "y": card_y}, {"card": "Qh", "x": card_x[1], "y": card_y},
                    {"card": "7h", "x": card_x[2], "y": card_y}, {"card": "5h", "x": card_x[3], "y": card_y},
                    {"card": "2h", "x": card_x[4], "y": card_y},
                ]
            },
             {
                "title": "HAND RANKING: STRAIGHT",
                "text": ["Five cards in sequence,", "but not all the same suit.", "(Ace can be high or low: A2345)", "", "Click or Press Key to Continue..."],
                "group_label": "Straight (Ace High)",
                "visuals": [
                    {"card": "As", "x": card_x[0], "y": card_y}, {"card": "Kh", "x": card_x[1], "y": card_y},
                    {"card": "Qd", "x": card_x[2], "y": card_y}, {"card": "Jc", "x": card_x[3], "y": card_y},
                    {"card": "10s","x": card_x[4], "y": card_y},
                ]
            },
             {
                "title": "HAND RANKING: THREE OF A KIND",
                "text": ["Three cards of the same rank,", "plus two other unrelated cards.", "", "Click or Press Key to Continue..."],
                "group_label": "Three of a Kind (Jacks)",
                "visuals": [
                    {"card": "Jc", "x": card_x[0], "y": card_y}, {"card": "Jh", "x": card_x[1], "y": card_y},
                    {"card": "Jd", "x": card_x[2], "y": card_y}, # Three Jacks
                    {"card": "As", "x": card_x[3], "y": card_y}, {"card": "Kh", "x": card_x[4], "y": card_y}, # Kickers
                ]
            },
             {
                "title": "HAND RANKING: TWO PAIR",
                "text": ["Two cards of one rank,", "two cards of another rank,", "and one unrelated card.", "", "Click or Press Key to Continue..."],
                "group_label": "Two Pair (Aces and Kings)",
                "visuals": [
                    {"card": "As", "x": card_x[0], "y": card_y}, {"card": "Ah", "x": card_x[1], "y": card_y}, # Pair Aces
                    {"card": "Kh", "x": card_x[2], "y": card_y}, {"card": "Kd", "x": card_x[3], "y": card_y}, # Pair Kings
                    {"card": "Qs", "x": card_x[4], "y": card_y}, # Kicker
                ]
            },
             {
                "title": "HAND RANKING: ONE PAIR",
                "text": ["Two cards of the same rank,", "plus three other unrelated cards.", "", "Click or Press Key to Continue..."],
                "group_label": "One Pair (Queens)",
                "visuals": [
                    {"card": "Qs", "x": card_x[0], "y": card_y}, {"card": "Qh", "x": card_x[1], "y": card_y}, # Pair Queens
                    {"card": "As", "x": card_x[2], "y": card_y}, {"card": "Kh", "x": card_x[3], "y": card_y}, {"card": "Jc", "x": card_x[4], "y": card_y}, # Kickers
                ]
            },
             {
                "title": "HAND RANKING: HIGH CARD",
                "text": ["None of the above hands.", "The hand is valued by its", "highest ranking card.", "", "Click or Press Key to Continue..."],
                "group_label": "High Card (Ace High)",
                "visuals": [
                    # Ensure these cards are in cards_to_load
                    {"card": "As", "x": card_x[0], "y": card_y}, {"card": "Kh", "x": card_x[1], "y": card_y},
                    {"card": "Qd", "x": card_x[2], "y": card_y}, {"card": "Jc", "x": card_x[3], "y": card_y},
                    {"card": "9h", "x": card_x[4], "y": card_y},
                ]
            },
        ]

        page_betting = {
            "title": "BETTING ROUNDS",
             "text": [
                "1. Pre-Flop (After hole cards)",
                "2. Flop (After first 3 community cards)",
                "3. Turn (After 4th community card)",
                "4. River (After 5th community card)",
                "Actions:",
                "- Check (If no bet before you)",
                "- Bet / Raise",
                "- Call (Match current bet)",
                "- Fold (Discard hand)",
                "",
                "Click or Press Key to Continue..."
            ],
            "visuals": [
                {"card": "Jc", "x": 0.65, "y": 0.3, "label": "Pre-Flop"},
                {"card": "Qs", "x": 0.80, "y": 0.3, "label": "Pre-Flop"},
                {"card": "2h", "x": 0.25, "y": 0.75, "label": "Flop"},
                {"card": "10d", "x": 0.40, "y": 0.75, "label": "Flop"},
                {"card": "Kh", "x": 0.55, "y": 0.75, "label": "Flop"},
                {"card": "As", "x": 0.70, "y": 0.75, "label": "Turn"},
                {"card": "back", "x": 0.85, "y": 0.75, "label": "River"}
            ]
        }
        page_strategy = {
            "title": "GAME STRATEGY (Very Basic)",
            "text": [
                "Starting Hands: Play strong hands",
                "like A-A, K-K, Q-Q, J-J, A-K.",
                "Fold weak hands often.",
                "",
                "Position: Acting last is powerful.",
                "Play more hands in late position.",
                "",
                "Observation: Watch opponents.",
                "Are they tight? Loose? Aggressive?",
                "",
                "Bankroll: Only gamble what you",
                "can afford to lose.",
                "",
                "Press Esc to return | Click/Key to advance"
            ],
            "visuals": [
                 # Use cards available in cards_to_load
                {"card": "As", "x": 0.6, "y": 0.30, "label": "Premium"},
                {"card": "Ah", "x": 0.8, "y": 0.30, "label": "Premium"},
                {"card": "7d", "x": 0.6, "y": 0.65, "label": "Weak"},
                {"card": "2c", "x": 0.8, "y": 0.65, "label": "Weak"}
            ]
        }

        # --- Combine all pages in the desired order ---
        self.pages = [
            page_basics,
            page_rankings_intro
        ] + hand_pages + [ # Inserts the detailed hand pages list
            page_betting,
            page_strategy
        ]

        self.current_page_index = 0 # Start at the first page
        self.reposition_visuals(self.current_page_index) # Calculate initial positions
        print("Tutorial initialized successfully.")


    def load_card_back(self):
        """Loads and scales the card_back.jpg image."""
        card_width = max(self.MIN_CARD_WIDTH, int(self.screen_width * CARD_WIDTH_RATIO))
        card_height = max(self.MIN_CARD_HEIGHT, int(self.screen_height * CARD_HEIGHT_RATIO))
        fallback_surface = None
        try:
            script_dir = os.path.dirname(__file__)
            img_path = os.path.join(script_dir, "cards", "card_back.jpg")
            back_image = pygame.image.load(img_path).convert()
            self.example_cards["back"] = pygame.transform.smoothscale(back_image, (card_width, card_height))
        except (pygame.error, FileNotFoundError) as e:
            print(f"ERROR loading card back image '{img_path}': {e}")
            print("--> Using placeholder blue surface instead.")
            fallback_surface = pygame.Surface((card_width, card_height))
            fallback_surface.fill((70, 70, 255))
            pygame.draw.rect(fallback_surface, BLACK, fallback_surface.get_rect(), 2)
            self.example_cards["back"] = fallback_surface
        except Exception as e:
             print(f"Unexpected error loading card back: {e}")
             fallback_surface = pygame.Surface((card_width, card_height))
             fallback_surface.fill((255, 0, 0)) # Red error color
             self.example_cards["back"] = fallback_surface


    def update_sizes(self):
        """Updates screen dimensions, fonts, and resizes cards upon window resize."""
        current_w, current_h = self.screen.get_size()
        self.screen_width = max(MIN_WIDTH, current_w)
        self.screen_height = max(MIN_HEIGHT, current_h)

        # Recreate fonts based on the new height for scalability
        try:
            self.font_large = pygame.font.SysFont('Arial', int(self.screen_height * 0.08))
            self.font_medium = pygame.font.SysFont('Arial', int(self.screen_height * 0.05))
            self.font_small = pygame.font.SysFont('Arial', int(self.screen_height * 0.04))
            self.font_label = pygame.font.SysFont('Arial', int(self.screen_height * 0.03))
            self.font_group_label = pygame.font.SysFont('Arial', int(self.screen_height * 0.035), bold=True)
        except Exception as e:
            print(f"Error initializing fonts: {e}. Using default fonts.")
            # Fallback to default fonts if SysFont fails
            self.font_large = pygame.font.Font(None, 64)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 28)
            self.font_label = pygame.font.Font(None, 24)
            self.font_group_label = pygame.font.Font(None, 26)

        # Update size of all example FACE cards using their own update_size method
        if hasattr(self, 'example_cards'): # Check if dict exists
            for card_key, card_obj in self.example_cards.items():
                # Only update if it's a Card object (not None or the back Surface)
                if isinstance(card_obj, Card) and hasattr(card_obj, 'update_size'):
                    try:
                        card_obj.update_size(self.screen_width, self.screen_height)
                    except Exception as e:
                        print(f"Error updating size for card '{card_key}': {e}")

            # Reload/resize the card BACK separately using consistent logic
            self.load_card_back()


    def reposition_visuals(self, page_index):
        """Calculates and stores absolute pixel positions for visuals on the current page."""
        if not (hasattr(self, 'pages') and 0 <= page_index < len(self.pages)):
             return # Invalid index or pages not ready

        page = self.pages[page_index]

        if "visuals" in page:
            for visual in page["visuals"]:
                try:
                    # Ensure 'x' and 'y' keys exist before calculation
                    if "x" in visual and "y" in visual:
                        x_pos = int(visual["x"] * self.screen_width)
                        y_pos = int(visual["y"] * self.screen_height)
                        # Store calculated positions
                        visual["abs_x"] = x_pos
                        visual["abs_y"] = y_pos
                    else:
                        print(f"Warning: Visual missing 'x' or 'y' key in page {page_index}: {visual.get('card', 'N/A')}")
                        # Provide fallback positions maybe?
                        visual["abs_x"] = self.screen_width // 2
                        visual["abs_y"] = self.screen_height // 2
                except KeyError as e: # Should be caught by check above, but good practice
                    print(f"Error: Visual definition missing key {e} in page {page_index}.")
                except Exception as e:
                    print(f"Error calculating position for visual {visual.get('card', 'N/A')}: {e}")


    def draw_page(self, page_index):
        """Draws all elements (title, text, visuals) for the specified page index."""
        if not (hasattr(self, 'pages') and 0 <= page_index < len(self.pages)):
             # Draw error message if pages aren't ready
             self.screen.fill(BLACK)
             err_font = pygame.font.Font(None, 30)
             err_surf = err_font.render("Error loading tutorial page data.", True, WHITE)
             err_rect = err_surf.get_rect(center=(self.screen_width//2, self.screen_height//2))
             self.screen.blit(err_surf, err_rect)
             return

        page = self.pages[page_index]
        self.screen.fill(DARK_GREEN)

        # --- Draw Title ---
        if hasattr(self, 'font_large'):
            try:
                title_text = page.get("title", "No Title")
                title_surface = self.font_large.render(title_text, True, WHITE)
                title_rect = title_surface.get_rect(center=(self.screen_width // 2, int(self.screen_height * 0.07)))
                self.screen.blit(title_surface, title_rect)
            except Exception as e:
                print(f"Error drawing title '{page.get('title', '')}': {e}")
        else:
            print("Warning: font_large not initialized.")

        # --- Draw Text Block ---
        text_y_start_default = int(self.screen_height * 0.18)
        # Adjust text start position if there's a group label to make space
        text_y_start = text_y_start_default if 'group_label' not in page else int(self.screen_height * 0.12)

        if hasattr(self, 'font_medium') and hasattr(self, 'font_small'):
            text_x = int(self.screen_width * 0.05)
            line_height_large = int(self.screen_height * 0.06)
            line_height_small = int(self.screen_height * 0.045)
            y_pos = text_y_start

            for line in page.get("text", ["Error: Text missing."]):
                try:
                    is_bullet = line.strip().startswith("-")
                    render_font = None
                    render_line = ""
                    line_spacing = line_height_small # Default spacing

                    if is_bullet:
                        render_font = self.font_small
                        render_line = "  " + line.strip()
                        line_spacing = line_height_small
                    elif line == "":
                        # It's an empty line for spacing, don't render text
                        line_spacing = line_height_small * 0.5
                    else:
                        render_font = self.font_medium
                        render_line = line
                        line_spacing = line_height_large

                    if render_font and render_line: # Check we have font and text to render
                        text_surface = render_font.render(render_line, True, WHITE)
                        self.screen.blit(text_surface, (text_x, y_pos))

                    y_pos += line_spacing # Move down for the next line
                except Exception as e:
                    print(f"Error rendering text line '{line}': {e}")
                    y_pos += line_height_small # Advance position even on error
        else:
            print("Warning: text fonts (medium/small) not initialized.")


        # --- Draw Visuals & Labels ---
        max_card_y = 0 # Track lowest point of cards
        visual_area_x_min = self.screen_width # Track horizontal bounds
        visual_area_x_max = 0

        if "visuals" in page and hasattr(self, 'example_cards') and hasattr(self, 'font_label'):
            for visual in page["visuals"]:
                try:
                    # Use pre-calculated absolute positions
                    x_pos = visual.get("abs_x")
                    y_pos = visual.get("abs_y")
                    card_key = visual.get("card")

                    # Check if essential data is present
                    if x_pos is None or y_pos is None or card_key is None:
                        print(f"Warning: Skipping visual due to missing data (x, y, or card) in page {page_index}: {visual}")
                        continue

                    image_to_draw = self.example_cards.get(card_key)

                    # Determine dimensions for drawing and label positioning
                    img_height = self.MIN_CARD_HEIGHT
                    img_width = self.MIN_CARD_WIDTH

                    # --- Draw the card/back/placeholder ---
                    if image_to_draw:
                        if isinstance(image_to_draw, Card):
                            if image_to_draw.image:
                                img_surface = image_to_draw.image
                                img_height = img_surface.get_height()
                                img_width = img_surface.get_width()
                                # Set Card's internal coords before drawing
                                image_to_draw.x = x_pos
                                image_to_draw.y = y_pos
                                image_to_draw.draw(self.screen) # Use Card's method
                            else:
                                # Card object exists but image failed? Draw placeholder.
                                pygame.draw.rect(self.screen, RED, (x_pos, y_pos, img_width, img_height), 2)
                                # Error already printed during init/update_sizes
                        elif isinstance(image_to_draw, pygame.Surface):
                             # It's the card back (or a fallback surface)
                            img_surface = image_to_draw
                            img_height = img_surface.get_height()
                            img_width = img_surface.get_width()
                            self.screen.blit(img_surface, (x_pos, y_pos)) # Draw Surface
                        else:
                             # Unexpected type
                             pygame.draw.rect(self.screen, RED, (x_pos, y_pos, img_width, img_height))
                             print(f"Warning: Visual '{card_key}' is neither Card nor Surface.")
                    else:
                        # Card key was in visuals, but not found in example_cards (likely missing image file)
                        pygame.draw.rect(self.screen, RED, (x_pos, y_pos, img_width, img_height))
                        # Warning printed during init, no need to repeat here unless debugging

                    # --- Update bounds for group label ---
                    max_card_y = max(max_card_y, y_pos + img_height)
                    visual_area_x_min = min(visual_area_x_min, x_pos)
                    visual_area_x_max = max(visual_area_x_max, x_pos + img_width)

                    # --- Draw INDIVIDUAL label if present ---
                    label_text = visual.get("label", "")
                    if label_text and hasattr(self, 'font_label'):
                        label_surface = self.font_label.render(label_text, True, WHITE)
                        label_rect = label_surface.get_rect(center=(x_pos + img_width // 2, y_pos + img_height + int(self.screen_height * 0.02)))
                        self.screen.blit(label_surface, label_rect)
                    elif label_text: # Font label exists but font object doesn't
                         print("Warning: font_label not initialized, cannot draw label.")

                except Exception as e:
                     print(f"Error drawing visual '{visual.get('card', 'N/A')}': {e}")
                     traceback.print_exc() # More details on error

        # --- Draw GROUP label if present ---
        group_label_text = page.get("group_label", "")
        if group_label_text and hasattr(self, 'font_group_label') and max_card_y > 0:
            try:
                 label_surface = self.font_group_label.render(group_label_text, True, WHITE)
                 # Center the group label horizontally under the drawn visuals
                 center_x = (visual_area_x_min + visual_area_x_max) // 2
                 # Position below the lowest card + a gap
                 center_y = max_card_y + int(self.screen_height * 0.04)
                 label_rect = label_surface.get_rect(center=(center_x, center_y))
                 self.screen.blit(label_surface, label_rect)
            except Exception as e:
                 print(f"Error drawing group label '{group_label_text}': {e}")
        elif group_label_text and not hasattr(self, 'font_group_label'):
             print("Warning: font_group_label not initialized, cannot draw group label.")


    def run(self):
        """Main loop for the tutorial screen."""
        if not self.running:
            print("Tutorial cannot run due to initialization errors.")
            return 'menu' # Or 'quit'

        # Ensure initial visuals are positioned correctly after all loading
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
                        self.update_sizes() # Updates fonts, card sizes
                        self.reposition_visuals(self.current_page_index) # Recalculate positions
                    except pygame.error as e:
                         print(f"Error resizing screen: {e}")

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return 'menu' # Signal return to main menu
                    else:
                        # Any other key advances the page
                        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
                        self.reposition_visuals(self.current_page_index) # Reposition for new page

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left mouse click advances page
                        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
                        self.reposition_visuals(self.current_page_index) # Reposition for new page

            # --- Drawing ---
            try:
                 self.draw_page(self.current_page_index)
            except Exception as e:
                 print(f"FATAL DRAW ERROR on page {self.current_page_index}: {e}")
                 traceback.print_exc()
                 # Draw an error message on screen
                 self.screen.fill(BLACK)
                 err_font = pygame.font.Font(None, 30)
                 err_surf = err_font.render(f"Draw Error page {self.current_page_index}. Check console.", True, RED)
                 err_rect = err_surf.get_rect(center=(self.screen_width//2, self.screen_height//2))
                 self.screen.blit(err_surf, err_rect)
                 # Stop the loop to prevent continuous errors
                 self.running = False # Set running to False here

            # --- Update Display ---
            pygame.display.flip()

            # --- Frame Rate Control ---
            self.clock.tick(FPS)

        # Loop finished (either by Esc, Quit, or Draw Error)
        return 'menu' # Default return action


# ======================================================
# Main Execution Block (for testing the tutorial directly)
# ======================================================
if __name__ == "__main__":
    print("Running TexasHoldemTutorial directly for testing...")
    pygame.init()
    pygame.font.init() # Explicitly initialize font module
    screen = None # Initialize screen to None
    try:
        screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Texas Hold'em Tutorial (Test Mode)")
        tutorial = TexasHoldemTutorial(screen)

        if tutorial.running: # Check if init succeeded
            result = tutorial.run() # Start the tutorial loop
            print(f"Tutorial finished with result: {result}")
        else:
            print("Tutorial initialization failed. Cannot run.")
            pygame.time.wait(5000) # Keep window open to see console errors

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
         traceback.print_exc() # Print detailed traceback
    finally:
        print("Quitting Pygame.")
        pygame.quit() # Cleanly exit Pygame

# --- END OF FILE TexasHoldemTutorial.py ---