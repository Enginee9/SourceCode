# --- START OF FILE PokerGUI.py ---

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, font, Text
import time
import random
import os
import traceback # Import traceback for detailed error printing

# --- Attempt to import Pillow (PIL) ---
try:
    from PIL import Image, ImageTk
except ImportError:
    # Use tkinter's built-in messagebox if available early
    try:
        import tkinter.messagebox
        tkinter.messagebox.showerror("Error", "Pillow library not found.\nPlease install it: pip install Pillow")
    except Exception: # Fallback if even tkinter isn't fully working
        print("ERROR: Pillow library not found. Please install it: pip install Pillow")
    exit() # Exit if Pillow is missing

# --- Import Game Logic Components ---
try:
    # Ensure these files are in the same directory or Python path
    from MatchManager_GUI import PokerGame, INITIAL_HEARTS
    from BotPlayer import BotPlayer
    from HandEvaluator import HandEvaluator
    from Deck import Deck
except ImportError as e:
     # Use tkinter's built-in messagebox if available
     try:
         import tkinter.messagebox
         tkinter.messagebox.showerror("Import Error", f"Failed to import game logic components: {e}\nMake sure MatchManager_GUI.py, BotPlayer.py, HandEvaluator.py, Deck.py are accessible.")
     except Exception:
          print(f"IMPORT ERROR: Failed to import game logic components: {e}\nMake sure MatchManager_GUI.py, BotPlayer.py, HandEvaluator.py, Deck.py are accessible.")
     exit() # Exit if game logic is missing

class PokerGUI:
    # --- Constants ---
    CARD_WIDTH = 72
    CARD_HEIGHT = 100
    TABLE_GREEN = "#121212" # Dark background color
    HEART_ICON = "♥"
    SEQ_FONT_NORMAL = ("Arial", 16)
    SEQ_FONT_DEVIL = ("Arial", 18, "bold")
    SEQ_COLOR_DEVIL = "#FF4444"
    SEQ_COLOR_NARRATOR = "#CCCCCC"
    SEQ_COLOR_MAN = "#AAAAFF"
    SEQ_COLOR_DEFAULT = "#FFFFFF"
    STARTING_CHIPS = 1000 # Default starting chips

    def __init__(self, root):
        """Initializes the Poker GUI within the provided Tkinter root (Toplevel window)."""
        self.root = root # This root is the Toplevel window passed from MainMenu
        self.root.title("Poker Game - Devil's Deal")
        self.root.geometry("1280x800") # Set initial size

        self.image_dir = "cards" # Subdirectory for card images
        self.card_images = {} # Dictionary to hold loaded card images
        self.card_back_image = None # To hold the loaded card back image
        self._load_card_images() # Load images immediately

        # --- Font Definitions ---
        try:
            self.status_font = font.Font(family="Arial", size=12)
            self.heart_font = font.Font(family="Arial", size=14, weight="bold")
            self.log_font = font.Font(family="Consolas", size=9) # Monospaced font for log
        except tk.TclError: # Fallback if system fonts aren't found
            print("Warning: Arial/Consolas font not found, using default.")
            self.status_font = font.Font(size=12)
            self.heart_font = font.Font(size=14, weight="bold")
            self.log_font = font.Font(size=9)

        # --- Game State Variables ---
        self.game = None # Will hold the PokerGame instance
        self.player_name = "Player" # Default player name
        self.bot_count = 1 # Default bot count
        self.bot_difficulty = "easy" # Default bot difficulty
        self.turn_order = [] # Stores player names in turn order for the round
        self.current_player_index = 0 # Index into turn_order
        self.current_round_name = "" # e.g., "preflop", "flop", "turn", "river", "showdown"
        self.human_action_taken = False # Flag to prevent duplicate actions on clicks

        # --- UI Frames ---
        self.setup_frame = ttk.Frame(root, padding="10") # For game setup options
        self.game_frame = ttk.Frame(root, padding="10", style="Game.TFrame") # Main game area
        self.log_frame = ttk.Frame(root, padding="5") # Frame for the message log
        # Widgets for ending sequence (created later)
        self.ending_frame = None
        self.ending_text_widget = None
        self.ending_script_lines = []
        self.ending_current_line = 0
        self.ending_after_id = None # ID for scheduled ending text display

        # --- Style Configuration (using ttk for better appearance) ---
        self.style = ttk.Style()
        self.style.configure("Game.TFrame", background=self.TABLE_GREEN)
        self.style.configure("GreenBG.TLabel", background=self.TABLE_GREEN, foreground="white")
        self.style.configure("GreenBG.TLabelframe", background=self.TABLE_GREEN)
        # Label *inside* the Labelframe needs styling too
        self.style.configure("GreenBG.TLabelframe.Label", background=self.TABLE_GREEN, foreground="white")
        # Style for the hearts label
        self.style.configure("Hearts.TLabel", background=self.TABLE_GREEN, foreground="#FF6347", font=self.heart_font)

        # --- Log Area Setup ---
        self.log_text = Text(self.log_frame, height=8, width=110, wrap=tk.WORD, font=self.log_font,
                             relief=tk.SUNKEN, borderwidth=1, state=tk.DISABLED,
                             bg="#222222", fg="#DDDDDD") # Darker log background
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=self.log_scroll.set)
        # Grid layout for log text and scrollbar within log_frame
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_scroll.grid(row=0, column=1, sticky="ns")
        # Make log text area expand
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        # --- Initial Frame Layout ---
        # Pack log at bottom, setup frame fills the rest initially
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)
        self.setup_frame.pack(fill=tk.BOTH, expand=True)

        # Create the widgets for setup and game screens (game widgets are hidden initially)
        self._create_setup_widgets()
        self._create_game_widgets()

        # Window close ('X' button) is handled by MainMenu using protocol on the Toplevel

    def _load_card_images(self):
        """Loads and resizes card images from the 'cards' directory."""
        if not os.path.isdir(self.image_dir):
            messagebox.showerror("Error", f"Image directory '{self.image_dir}' not found.")
            self.root.quit() # Cannot proceed without images
            return

        # Maps for converting between internal representation and filenames
        rank_map_file = {'A': 'ace', 'K': 'king', 'Q': 'queen', 'J': 'jack', 'T': '10', '9': '9', '8': '8', '7': '7', '6': '6', '5': '5', '4': '4', '3': '3', '2': '2'}
        suit_map_file = {'h': 'hearts', 'd': 'diamonds', 'c': 'clubs', 's': 'spades'}
        # Internal shorthand codes (used in game logic and as keys here)
        shorthand_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        shorthand_suits = ['h', 'd', 'c', 's']
        loaded_count = 0
        expected_count = len(shorthand_ranks) * len(shorthand_suits) + 1 # +1 for card back
        missing_files = []

        # Load face cards
        for rank_short in shorthand_ranks:
            for suit_short in shorthand_suits:
                card_shorthand = f"{rank_short}{suit_short}" # e.g., "As", "Th", "2c"
                rank_file = rank_map_file.get(rank_short)
                suit_file = suit_map_file.get(suit_short)
                if not rank_file or not suit_file:
                    print(f"Warning: Invalid rank/suit shorthand: {rank_short}{suit_short}")
                    continue # Skip if shorthand isn't recognized

                filename = f"{rank_file}_of_{suit_file}.jpg" # Construct filename (e.g., ace_of_spades.jpg)
                file_path = os.path.join(self.image_dir, filename)

                try:
                    # Open, resize, and convert to PhotoImage
                    img = Image.open(file_path)
                    img = img.resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS) # High-quality resize
                    self.card_images[card_shorthand] = ImageTk.PhotoImage(img)
                    loaded_count += 1
                except FileNotFoundError:
                    # Log missing file but continue
                    print(f"Warning: Image file not found: {file_path}")
                    if filename not in missing_files: missing_files.append(filename)
                    self.card_images[card_shorthand] = None # Store None placeholder
                except Exception as e:
                    # Log other loading errors
                    print(f"Warning: Failed to load/resize image {file_path}: {e}")
                    if filename not in missing_files: missing_files.append(filename)
                    self.card_images[card_shorthand] = None # Store None placeholder

        # Load card back
        card_back_path = os.path.join(self.image_dir, "card_back.jpg")
        try:
            img = Image.open(card_back_path)
            img = img.resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS)
            self.card_back_image = ImageTk.PhotoImage(img)
            loaded_count += 1
        except FileNotFoundError:
            print(f"ERROR: Card back image file not found: {card_back_path}")
            messagebox.showwarning("Image Error", f"Card back ({card_back_path}) not found.\nHidden cards will be blank.")
            self.card_back_image = None # Set to None if missing
            if "card_back.jpg" not in missing_files: missing_files.append("card_back.jpg")
        except Exception as e:
            print(f"ERROR: Failed to load/resize card back image {card_back_path}: {e}")
            messagebox.showwarning("Image Error", f"Failed to load card back: {e}")
            self.card_back_image = None
            if "card_back.jpg" not in missing_files: missing_files.append("card_back.jpg")


        print(f"Loaded {loaded_count}/{expected_count} card images.")
        if missing_files:
             # Show a summary warning if any images failed
             warning_msg = "Failed to load the following card images:\n"
             warning_msg += "\n".join(f"- {fname}" for fname in sorted(missing_files))
             warning_msg += "\n\nPlaceholders will be used. Check console and 'cards' folder."
             messagebox.showwarning("Image Load Warning", warning_msg)

    def _create_setup_widgets(self):
        """Creates the widgets for the initial game setup screen."""
        # Center elements in the setup frame
        self.setup_frame.columnconfigure(0, weight=1)
        self.setup_frame.columnconfigure(1, weight=1)

        # Title
        ttk.Label(self.setup_frame, text="Poker Setup - Devil's Deal", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        # Player Name Input
        ttk.Label(self.setup_frame, text="Your Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(self.setup_frame, width=30)
        self.name_entry.insert(0, self.player_name) # Pre-fill with default
        self.name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Bot Count Selection
        ttk.Label(self.setup_frame, text="Number of Bots:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.bot_count_var = tk.IntVar(value=self.bot_count) # Variable to store selection
        bot_count_frame = ttk.Frame(self.setup_frame) # Frame to hold radio buttons
        # Create radio buttons for 1, 2, or 3 bots
        for i in range(1, 4):
             ttk.Radiobutton(bot_count_frame, text=str(i), variable=self.bot_count_var, value=i).pack(side=tk.LEFT, padx=5)
        bot_count_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Bot Difficulty Selection
        ttk.Label(self.setup_frame, text="Bot Difficulty:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.bot_difficulty_var = tk.StringVar(value=self.bot_difficulty) # Variable for difficulty
        difficulty_frame = ttk.Frame(self.setup_frame)
        ttk.Radiobutton(difficulty_frame, text="Easy", variable=self.bot_difficulty_var, value="easy").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(difficulty_frame, text="Hard", variable=self.bot_difficulty_var, value="hard").pack(side=tk.LEFT, padx=5)
        difficulty_frame.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Start Game Button
        self.start_button = ttk.Button(self.setup_frame, text="Make the Deal", command=self.start_game)
        self.start_button.grid(row=4, column=0, columnspan=2, pady=20)

    def _create_game_widgets(self):
        """Creates the widgets for the main game screen (initially hidden)."""
        # --- Grid Configuration for Game Frame ---
        # 3 columns, 4 rows (last row minimal height for button)
        self.game_frame.columnconfigure(0, weight=1) # Left Bot Area / Exit Button Col
        self.game_frame.columnconfigure(1, weight=1) # Center Area (Community Cards, Pot) Col
        self.game_frame.columnconfigure(2, weight=1) # Right Bot Area Col
        self.game_frame.rowconfigure(0, weight=1) # Top Bot Area Row
        self.game_frame.rowconfigure(1, weight=1) # Middle Area Row (Pot/Info, maybe Bot)
        self.game_frame.rowconfigure(2, weight=3) # Player Area Row (more weight)
        self.game_frame.rowconfigure(3, weight=0) # Bottom Row for Return Button

        # --- Community Card Area (Center Top) ---
        community_frame = ttk.LabelFrame(self.game_frame, text="Community Cards", padding="5", style="GreenBG.TLabelframe")
        # Place in center column, spanning top two rows initially
        community_frame.grid(row=0, column=1, rowspan=1, pady=5, sticky="nsew") # Adjusted rowspan to 1
        self.community_card_labels = []
        # Inner frame to help center the cards within the LabelFrame
        card_area_frame = ttk.Frame(community_frame, style="Game.TFrame")
        card_area_frame.pack(expand=True, pady=5) # Center the card frame
        for i in range(5):
            # Create label, use card back image initially
            lbl = ttk.Label(card_area_frame, image=self.card_back_image, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = self.card_back_image # Keep reference
            lbl.pack(side=tk.LEFT, padx=3)
            self.community_card_labels.append(lbl)

        # --- Pot and Bet Info Area (Center Middle) ---
        info_frame = ttk.Frame(self.game_frame, padding="5", style="Game.TFrame")
        info_frame.grid(row=1, column=1, pady=5, sticky="n") # Place below community cards
        info_frame.columnconfigure(0, weight=1) # Make labels expand horizontally
        self.pot_label = ttk.Label(info_frame, text="Pot: 0", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.pot_label.grid(row=0, column=0, pady=1, sticky="ew")
        self.current_bet_label = ttk.Label(info_frame, text="Current Bet: 0", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.current_bet_label.grid(row=1, column=0, pady=1, sticky="ew")
        self.current_turn_label = ttk.Label(info_frame, text="Turn: -", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.current_turn_label.grid(row=2, column=0, pady=1, sticky="ew")

        # --- Player Area (Bottom Row spanning columns) ---
        player_frame = ttk.LabelFrame(self.game_frame, text="You", padding="10", style="GreenBG.TLabelframe")
        player_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="nsew")
        # Configure columns inside player frame for layout
        player_frame.columnconfigure(0, weight=1) # Stats area
        player_frame.columnconfigure(1, weight=2) # Cards area (wider)
        player_frame.columnconfigure(2, weight=1) # Actions area

        # Player Stats (Left side of Player Area)
        player_stats_frame = ttk.Frame(player_frame, style="Game.TFrame")
        player_stats_frame.grid(row=0, column=0, sticky="nw", padx=10, pady=5)
        self.player_chips_label = ttk.Label(player_stats_frame, text=f"Chips: {self.STARTING_CHIPS}", font=self.status_font, style="GreenBG.TLabel")
        self.player_chips_label.pack(anchor="w", pady=2)
        self.player_hearts_label = ttk.Label(player_stats_frame, text=f"Hearts: {self.HEART_ICON * INITIAL_HEARTS}", style="Hearts.TLabel")
        self.player_hearts_label.pack(anchor="w", pady=2)

        # Player Cards (Center of Player Area)
        cards_frame = ttk.Frame(player_frame, style="Game.TFrame")
        cards_frame.grid(row=0, column=1, pady=5, sticky="n") # Center horizontally
        self.player_card_labels = []
        for i in range(2):
            lbl = ttk.Label(cards_frame, image=self.card_back_image, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = self.card_back_image
            lbl.pack(side=tk.LEFT, padx=5)
            self.player_card_labels.append(lbl)

        # Action Buttons (Right side of Player Area)
        action_frame = ttk.Frame(player_frame, style="Game.TFrame")
        action_frame.grid(row=0, column=2, padx=10, pady=5, sticky="ne")
        # Create buttons, initially disabled
        self.check_button = ttk.Button(action_frame, text="Check", command=lambda: self.handle_human_action("check", 0), state=tk.DISABLED)
        self.check_button.pack(pady=2, fill=tk.X)
        self.call_button = ttk.Button(action_frame, text="Call", command=lambda: self.handle_human_action("call", 0), state=tk.DISABLED)
        self.call_button.pack(pady=2, fill=tk.X)
        self.fold_button = ttk.Button(action_frame, text="Fold", command=lambda: self.handle_human_action("fold", 0), state=tk.DISABLED)
        self.fold_button.pack(pady=2, fill=tk.X)
        # Frame for Raise button and entry field
        raise_frame = ttk.Frame(action_frame, style="Game.TFrame")
        raise_frame.pack(pady=2, fill=tk.X)
        self.raise_button = ttk.Button(raise_frame, text="Raise", command=self.handle_raise_prompt, state=tk.DISABLED)
        self.raise_button.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.raise_amount_var = tk.StringVar() # Variable for raise amount entry
        self.raise_entry = ttk.Entry(raise_frame, width=7, textvariable=self.raise_amount_var, state=tk.DISABLED)
        self.raise_entry.pack(side=tk.LEFT, padx=(3,0))
        self.all_in_button = ttk.Button(action_frame, text="All In", command=lambda: self.handle_human_action("all in", 0), state=tk.DISABLED)
        self.all_in_button.pack(pady=2, fill=tk.X)

        # --- Bot Area Placeholders ---
        # Store widgets for up to 3 bots, but don't grid them yet
        self.bot_widgets = {}
        # Define intended grid positions for layout logic later
        self._create_bot_area_placeholder("Bot_1", 0, 0) # Top Left
        self._create_bot_area_placeholder("Bot_2", 0, 2) # Top Right
        self._create_bot_area_placeholder("Bot_3", 1, 0) # Mid Left (below Bot 1)

        # --- Return to Menu Button (Bottom Row, Left Column) ---
        self.return_button = ttk.Button(self.game_frame,
                                        text="Return to Menu", # Changed text
                                        command=self._return_to_menu) # Use the new method
        self.return_button.grid(row=3, column=0, padx=10, pady=10, sticky="sw") # Place at bottom-left

    def _create_bot_area_placeholder(self, placeholder_name, grid_row, grid_col):
        """Creates the widgets for a bot display area but doesn't grid it."""
        # Create a LabelFrame for the bot
        frame = ttk.LabelFrame(self.game_frame, text=placeholder_name, padding="5", style="GreenBG.TLabelframe")

        # Label for chips/info
        info_label = ttk.Label(frame, text=f"Chips: {self.STARTING_CHIPS}", font=self.status_font, anchor="w", style="GreenBG.TLabel")
        info_label.pack(pady=2, fill=tk.X)

        # Label for current status (e.g., Folded, All In, Active)
        status_label = ttk.Label(frame, text="Status: Waiting", font=self.status_font, anchor="w", style="GreenBG.TLabel")
        status_label.pack(pady=2, fill=tk.X)

        # Frame to hold the bot's card labels
        cards_frame = ttk.Frame(frame, style="Game.TFrame")
        cards_frame.pack(pady=5)
        card_labels = []
        for i in range(2): # Bots have 2 hole cards
            lbl = ttk.Label(cards_frame, image=self.card_back_image, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = self.card_back_image # Keep reference
            lbl.pack(side=tk.LEFT, padx=3)
            card_labels.append(lbl)

        # Store all created widgets and intended position in the dictionary
        self.bot_widgets[placeholder_name] = {
            'frame': frame,
            'info_label': info_label,
            'status_label': status_label,
            'card_labels': card_labels,
            'intended_row': grid_row, # Store where it *should* go
            'intended_col': grid_col
        }

    def add_log_message(self, message):
        """Appends a message to the log text area, handling potential widget errors."""
        if self.log_text and self.log_text.winfo_exists(): # Check if widget exists
            try:
                self.log_text.config(state=tk.NORMAL) # Enable writing
                self.log_text.insert(tk.END, message + "\n") # Add message and newline
                self.log_text.see(tk.END) # Scroll to the end
                self.log_text.config(state=tk.DISABLED) # Disable writing again
            except tk.TclError:
                # Handle error if widget is destroyed during the operation
                print("Log widget error (likely closing):", message)
        else:
            # Log to console if GUI widget is not available
            print(f"LOG (GUI not ready): {message}")

    def start_game(self):
        """Gets setup options, initializes the PokerGame instance, and switches view."""
        self.player_name = self.name_entry.get().strip() or "Player" # Get name, default if empty
        self.bot_count = self.bot_count_var.get()
        self.bot_difficulty = self.bot_difficulty_var.get()

        self.game = None # Ensure game object is reset
        try:
            # Debug print for verification
            print(f"DEBUG GUI: Creating PokerGame with P:{self.player_name}, B:{self.bot_count}, D:{self.bot_difficulty}, H:{INITIAL_HEARTS}, C:{self.STARTING_CHIPS}")

            # Initialize the backend game logic object
            self.game = PokerGame(
                player_name=self.player_name,
                bot_count=self.bot_count,
                bot_difficulty=self.bot_difficulty,
                initial_hearts=INITIAL_HEARTS,
                initial_chips=self.STARTING_CHIPS # Pass starting chips
            )
            # No separate setup_game_gui call needed if constructor does setup

        except NameError as e:
             messagebox.showerror("Setup Error", f"A required name is not defined (check imports/constants): {e}")
             traceback.print_exc()
             self.game = None; return # Stop if setup fails
        except TypeError as e:
             messagebox.showerror("Setup Error", f"Mismatch in arguments for PokerGame setup: {e}\nCheck PokerGame.__init__ signature.")
             traceback.print_exc()
             self.game = None; return # Stop if setup fails
        except Exception as e:
            messagebox.showerror("Setup Error", f"Failed to set up game: {e}")
            traceback.print_exc()
            self.game = None; return # Stop if setup fails

        # --- Configure Bot Displays based on actual game setup ---
        self._configure_bot_displays() # Place bot widgets correctly

        # --- Switch from Setup View to Game View ---
        self.setup_frame.pack_forget() # Hide setup widgets
        self.game_frame.pack(fill=tk.BOTH, expand=True) # Show game widgets
        # Ensure log frame is visible below game frame
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)

        # Log initial messages
        self.add_log_message(f"--- Game Started: {self.player_name} vs {self.bot_count} Bot(s) ({self.bot_difficulty}) ---")
        self.add_log_message(f"Starting with {self.STARTING_CHIPS} chips and {INITIAL_HEARTS} hearts.")
        self.add_log_message("The Devil deals...")

        # Start the first round of the game
        self.start_new_round()

    def _configure_bot_displays(self):
        """Grids the bot frames in their intended positions based on the number of bots."""
        # Hide all placeholders first
        for widgets in self.bot_widgets.values():
             if widgets['frame'].winfo_exists():
                 widgets['frame'].grid_forget()

        if not self.game:
            print("ERROR: _configure_bot_displays called but self.game is None.")
            return

        # Get actual bot names from the game instance
        bot_names_in_game = []
        # Prefer checking the 'bots' list if it exists (contains BotPlayer objects)
        if hasattr(self.game, 'bots') and self.game.bots:
            bot_names_in_game = [b.name for b in self.game.bots]
        # Fallback: check the 'players' dictionary if it holds bot info
        elif hasattr(self.game, 'players'):
            bot_names_in_game = [name for name, p_data in self.game.players.items() if p_data.get('is_bot')]

        if not bot_names_in_game:
             print("DEBUG GUI: No bot names found in game instance for display configuration.")
             return

        # Map actual bot names to placeholder widgets based on intended positions
        placeholder_keys = list(self.bot_widgets.keys()) # ["Bot_1", "Bot_2", "Bot_3"]

        # Grid the frames for the actual number of bots created
        for i, actual_bot_name in enumerate(bot_names_in_game):
            if i < len(placeholder_keys):
                 placeholder_key = placeholder_keys[i] # Get the corresponding placeholder key
                 widgets_to_place = self.bot_widgets[placeholder_key]
                 # Get the row/column stored during placeholder creation
                 grid_row = widgets_to_place['intended_row']
                 grid_col = widgets_to_place['intended_col']

                 widgets_to_place['frame'].config(text=actual_bot_name) # Set the LabelFrame title
                 # Place the bot's frame onto the main game_frame grid
                 widgets_to_place['frame'].grid(row=grid_row, column=grid_col, padx=5, pady=5, sticky="nsew")
                 print(f"DEBUG GUI: Placed bot '{actual_bot_name}' at grid ({grid_row},{grid_col}) using placeholder {placeholder_key}")
            else:
                 # This case handles if self.bot_count was > 3 (more bots than placeholders)
                 print(f"Warning: More bots ({len(bot_names_in_game)}) than defined placeholders ({len(placeholder_keys)}). Bot '{actual_bot_name}' not displayed.")
                 break # Stop trying to place bots if we run out of placeholders

    def start_new_round(self):
        """Initiates a new round in the game logic and updates the UI."""
        if not self.game:
            print("ERROR: start_new_round called but game logic is not initialized.")
            return

        # Check game over status before starting a new round
        is_over, _, _ = self.game.check_game_over_status()
        if is_over:
            print("DEBUG GUI: start_new_round found game is already over.")
            self.check_game_over() # Trigger game over sequence if needed
            return

        self.add_log_message("\n" + "="*15 + " Starting New Round " + "="*15)
        try:
            # Tell the backend to reset for a new round and get initial info
            round_info = self.game.start_new_round_get_info()

            # Validate the received information
            if not round_info or 'error' in round_info:
                err_msg = round_info.get('error', 'Unknown error starting round.') if round_info else 'No round info returned.'
                messagebox.showerror("Round Error", err_msg)
                # If backend reports game over, ensure GUI reflects it
                if round_info and round_info.get('game_over'):
                    self.game.game_over = True
                else:
                    # Assume fatal error if round start fails critically
                    self.game.game_over = True
                self.check_game_over()
                return

            # --- Store turn order information for this round ---
            self.turn_order = round_info.get('turn_order', [])
            self.current_player_index = round_info.get('start_index', -1)
            # ---

            # Log blinds information
            dealer_name = round_info.get('dealer', '?')
            sb_player = round_info.get('sb_player', '?')
            sb_amount = round_info.get('sb_amount', '?')
            bb_player = round_info.get('bb_player', '?')
            bb_amount = round_info.get('bb_amount', '?')

            # Check if turn order is valid, essential for gameplay flow
            if not self.turn_order or self.current_player_index < 0:
                 print("Warning GUI: StartNewRound returned invalid turn order or start index.")
                 self.current_round_name = self.game.current_stage if self.game else "N/A"
                 self.update_ui()
                 # If no valid turn order, proceed cautiously, maybe betting is over?
                 self.root.after(100, self.process_next_turn)
                 return

            # Log the blinds posting messages
            self.add_log_message(f"Dealer button is on {dealer_name}.")
            self.add_log_message(f"{sb_player} posts small blind {sb_amount}.")
            self.add_log_message(f"{bb_player} posts big blind {bb_amount}.")

            self.current_round_name = self.game.current_stage # Update internal stage tracking
            self.update_ui() # Refresh the entire UI for the new round start
            self.root.update() # Ensure UI draws immediately

            # Trigger the first turn processing after a short delay
            self.root.after(200, self.process_next_turn) # Slightly longer delay

        except AttributeError as e:
            messagebox.showerror("Round Error", f"Game logic error (missing method/attribute): {e}")
            traceback.print_exc()
            if self.game: self.game.game_over = True
            self.check_game_over()
        except Exception as e:
            messagebox.showerror("Round Error", f"Unexpected error starting round: {e}")
            traceback.print_exc()
            if self.game: self.game.game_over = True
            self.check_game_over()

    def update_ui(self, show_bot_cards=False):
        """Refreshes all GUI elements based on the current game state from the backend."""
        if not self.game or not self.card_images:
            print("Warning: update_ui called but game or card images not ready.")
            return

        try:
            # Get the latest full game state summary from the backend
            state = self.game.get_game_state_summary()
            if not state or 'players' not in state:
                 print("Error: Invalid game state received in update_ui.")
                 # Maybe disable buttons or show error state?
                 self.disable_all_buttons()
                 self.pot_label.config(text="Pot: Error"); self.current_bet_label.config(text="Current Bet: Error")
                 self.current_turn_label.config(text="Turn: Error")
                 return

            # --- Update Center Info Area ---
            self.pot_label.config(text=f"Pot: {state.get('pot', 'N/A')}")
            self.current_bet_label.config(text=f"Current Bet: {state.get('current_bet', 'N/A')}")
            current_player_name = state.get('current_turn_player', "-") # Get current player from backend
            self.current_turn_label.config(text=f"Turn: {current_player_name}")
            self.current_round_name = state.get('current_stage', self.current_round_name) # Update displayed stage

            # --- Update Community Cards ---
            community_cards_data = state.get('community_cards', [])
            for i, lbl in enumerate(self.community_card_labels):
                img = self.card_back_image # Default to back
                card_code = None
                if i < len(community_cards_data):
                    card_code = community_cards_data[i] # Get card code like 'As' or 'Td'

                if card_code: # If there is a card for this position
                     img = self.card_images.get(card_code, self.card_back_image) # Get loaded image, fallback to back
                # Update label image (use back image if loaded image is None or card_code was None)
                final_img = img if img else self.card_back_image
                lbl.config(image=final_img)
                lbl.image = final_img # Keep reference

            # --- Update Player Area ---
            player_state_data = state['players'].get(self.player_name)
            if player_state_data:
                # Build status string (Folded / All In)
                status_text = ""
                if player_state_data.get('folded'): status_text = " (Folded)"
                if player_state_data.get('all_in'): status_text = " (ALL IN)"
                self.player_chips_label.config(text=f"Chips: {player_state_data.get('chips', 0)}{status_text}")
                hearts = player_state_data.get('hearts', 0)
                self.player_hearts_label.config(text=f"Hearts: {self.HEART_ICON * hearts}")
                # Update player hole cards
                player_cards_data = player_state_data.get('cards', [])
                for i, lbl in enumerate(self.player_card_labels):
                    img = self.card_back_image # Default to back
                    if i < len(player_cards_data) and player_cards_data[i]:
                        img = self.card_images.get(player_cards_data[i], self.card_back_image)
                    final_img = img if img else self.card_back_image
                    lbl.config(image=final_img)
                    lbl.image = final_img
            else:
                 # Handle case where player data might be missing
                 self.player_chips_label.config(text="Chips: -")
                 self.player_hearts_label.config(text="Hearts: -")

            # --- Update Bot Areas ---
            bot_names_in_game = [name for name, p_data in state['players'].items() if p_data.get('is_bot')]
            placeholder_keys = list(self.bot_widgets.keys()) # Get the placeholder keys ("Bot_1", etc.)

            for i, actual_bot_name in enumerate(bot_names_in_game):
                 if i < len(placeholder_keys): # Ensure we don't exceed placeholders
                      placeholder_key = placeholder_keys[i]
                      widgets = self.bot_widgets.get(placeholder_key) # Get the widgets dictionary
                      if not widgets: continue # Skip if placeholder somehow missing

                      bot_state_data = state['players'].get(actual_bot_name)
                      if bot_state_data:
                            # Build bot status text
                            status_text = "Active"
                            if bot_state_data.get('folded'): status_text = "Folded"
                            if bot_state_data.get('all_in'): status_text = "ALL IN"
                            widgets['info_label'].config(text=f"Chips: {bot_state_data.get('chips', 0)}")
                            widgets['status_label'].config(text=f"Status: {status_text}")
                            # Update bot cards (show back unless specified)
                            bot_cards_data = bot_state_data.get('cards', [])
                            for j, lbl in enumerate(widgets['card_labels']):
                                 img = self.card_back_image # Default to back
                                 # Show face card if showdown or explicitly requested
                                 if j < len(bot_cards_data) and bot_cards_data[j] and \
                                    (show_bot_cards or self.current_round_name == "showdown"):
                                     img = self.card_images.get(bot_cards_data[j], self.card_back_image)
                                 final_img = img if img else self.card_back_image
                                 lbl.config(image=final_img)
                                 lbl.image = final_img
                      else:
                            # Handle missing bot state data
                            widgets['info_label'].config(text="Chips: -")
                            widgets['status_label'].config(text="Status: Unknown")

            # --- Enable/Disable Action Buttons ---
            # Check if it's the human player's turn according to the backend
            if current_player_name == self.player_name and \
               not getattr(self.game, 'round_over', False) and \
               not getattr(self.game, 'game_over', False):

                # Double-check player status (not folded/all-in) from the *latest* state data
                player_state_now = state['players'].get(self.player_name)
                if player_state_now and not player_state_now.get('folded') and not player_state_now.get('all_in'):
                     # Player is active and it's their turn -> enable relevant buttons
                     print(f"DEBUG GUI: Enabling buttons for {self.player_name}")
                     self.update_action_buttons() # Logic to enable/disable specific buttons
                else:
                     # Player is folded or all-in, keep buttons disabled
                     print(f"DEBUG GUI: Disabling buttons for {self.player_name} (State: Folded/AllIn)")
                     self.disable_all_buttons()
            else:
                # Not the player's turn, or round/game is over
                self.disable_all_buttons()

        except tk.TclError as e:
            # Often happens if updating during window close
            print(f"TclError during UI update (likely closing window): {e}")
        except AttributeError as e:
            print(f"AttributeError during UI update (check game state structure): {e}")
            traceback.print_exc()
        except Exception as e:
            messagebox.showerror("UI Update Error", f"Unexpected error during UI update: {e}")
            traceback.print_exc()

    def update_action_buttons(self):
        """Enables/disables specific action buttons based on current game state and player chips."""
        if not self.game: return # Safety check

        try:
            state = self.game.get_game_state_summary()
            player_state = state['players'].get(self.player_name)

            # If player state is missing or player is inactive, disable all and return
            if not player_state or player_state.get('folded') or player_state.get('all_in'):
                 self.disable_all_buttons()
                 return

            # Get necessary values from state
            chips = player_state.get('chips', 0)
            current_bet = state.get('current_bet', 0) # Highest bet placed *this round* by anyone
            player_bet_this_round = player_state.get('current_round_bet', 0) # How much player put in *this round*
            # Amount needed to match the current highest bet
            amount_to_call = max(0, current_bet - player_bet_this_round)
            # Use big blind from game logic; provide a fallback if necessary
            big_blind = getattr(self.game, 'big_blind', 20)
            # Bet level before the current highest bet (for min raise calc)
            previous_bet = state.get('previous_bet', 0)

            # --- Enable/Disable Fold Button ---
            # Always possible if player is active
            self.fold_button.config(state=tk.NORMAL)

            # --- Enable/Disable Check / Call Buttons ---
            can_check = (amount_to_call <= 0) # Can check if no bet to call
            self.check_button.config(state=tk.NORMAL if can_check else tk.DISABLED)

            # Call button logic
            if not can_check: # There is a bet to call
                 # Calculate the actual cost (limited by player's chips)
                 actual_call_cost = min(amount_to_call, chips)
                 if chips >= amount_to_call: # Can afford the full call
                     self.call_button.config(state=tk.NORMAL, text=f"Call {amount_to_call}")
                 elif chips > 0: # Cannot afford full call, but can call with remaining chips (all-in)
                     self.call_button.config(state=tk.NORMAL, text=f"Call {chips} (All In)")
                 else: # No chips left, cannot call
                     self.call_button.config(state=tk.DISABLED, text="Call")
            else: # Check is available, so Call is disabled
                self.call_button.config(state=tk.DISABLED, text="Call")

            # --- Enable/Disable Raise / All-in Buttons ---
            # Can player *potentially* raise? (Must have more chips than needed to just call)
            can_potentially_raise = chips > amount_to_call

            if can_potentially_raise:
                # Calculate Minimum Legal Raise:
                # The raise must be at least as large as the previous bet/raise increment this round.
                # The minimum increment is typically the Big Blind.
                min_raise_increment = max(big_blind, current_bet - previous_bet if current_bet > previous_bet else big_blind)
                # The minimum *total bet* the player must make if they choose to raise.
                min_legal_total_bet_target = current_bet + min_raise_increment
                # The minimum *additional* chips needed beyond the call amount for this minimum raise.
                # Ensure it's at least 1 chip if a raise is intended.
                min_additional_chips_needed = max(1, min_legal_total_bet_target - player_bet_this_round) if min_legal_total_bet_target > player_bet_this_round else 0

                # Can the player afford the minimum *additional* chips?
                # Need enough chips to cover the call cost PLUS the minimum additional amount
                can_afford_minimum_raise = chips >= (amount_to_call + min_additional_chips_needed) if min_additional_chips_needed > 0 else False

                if can_afford_minimum_raise:
                     # Enable Raise button and entry
                     self.raise_button.config(state=tk.NORMAL, text=f"Raise (Min +{min_additional_chips_needed})")
                     self.raise_entry.config(state=tk.NORMAL)
                else:
                     # Cannot afford even the minimum raise, only call or all-in possible
                     self.raise_button.config(state=tk.DISABLED, text="Raise")
                     self.raise_entry.config(state=tk.DISABLED)
                     self.raise_amount_var.set("") # Clear entry
            else:
                # Cannot potentially raise (not enough chips over the call amount)
                self.raise_button.config(state=tk.DISABLED, text="Raise")
                self.raise_entry.config(state=tk.DISABLED)
                self.raise_amount_var.set("")

            # --- Enable/Disable All-in Button ---
            # Can always go all-in if player has chips
            if chips > 0:
                self.all_in_button.config(state=tk.NORMAL, text=f"All In ({chips})")
            else:
                 self.all_in_button.config(state=tk.DISABLED, text="All In")

        except Exception as e:
             print(f"Error updating action buttons: {e}")
             traceback.print_exc()
             self.disable_all_buttons() # Disable all on error

    def disable_all_buttons(self):
        """Disables all player action buttons."""
        # Check if widgets exist before configuring (safety for closing window)
        if hasattr(self, 'check_button') and self.check_button.winfo_exists():
            self.check_button.config(state=tk.DISABLED)
        if hasattr(self, 'call_button') and self.call_button.winfo_exists():
            self.call_button.config(state=tk.DISABLED, text="Call") # Reset text
        if hasattr(self, 'fold_button') and self.fold_button.winfo_exists():
            self.fold_button.config(state=tk.DISABLED)
        if hasattr(self, 'raise_button') and self.raise_button.winfo_exists():
            self.raise_button.config(state=tk.DISABLED, text="Raise") # Reset text
        if hasattr(self, 'raise_entry') and self.raise_entry.winfo_exists():
            self.raise_entry.config(state=tk.DISABLED)
            self.raise_amount_var.set("") # Clear any value
        if hasattr(self, 'all_in_button') and self.all_in_button.winfo_exists():
            self.all_in_button.config(state=tk.DISABLED, text="All In")

    def handle_human_action(self, action, total_bet_amount=0):
        """Processes the human player's chosen action by calling the backend."""
        # Basic checks: Game exists and isn't over
        if not self.game or self.game.game_over or self.game.round_over:
            print(f"DEBUG GUI: Action '{action}' ignored, game/round over.")
            return
        # Prevent double-clicks processing the same action
        if self.human_action_taken:
            print(f"DEBUG GUI: Action '{action}' ignored, action already taken this turn.")
            return

        # Verify with backend that it *is* the player's turn before proceeding
        try:
            current_state = self.game.get_game_state_summary()
            backend_turn = current_state.get('current_turn_player')
            if backend_turn != self.player_name:
                 print(f"ERROR GUI: handle_human_action called for {self.player_name} but backend turn is {backend_turn}. Ignoring.")
                 # Maybe re-enable buttons if UI got out of sync? Or just wait for backend update.
                 # self.update_ui() # Careful with potential loops
                 return
        except Exception as e:
            print(f"ERROR GUI: Failed verify turn in handle_human_action: {e}")
            return # Don't proceed if turn check fails

        # Mark action as taken and disable buttons immediately for responsiveness
        self.human_action_taken = True
        self.disable_all_buttons()

        # Get latest player state for calculations
        player_state = current_state['players'].get(self.player_name)
        if not player_state:
            print(f"ERROR GUI: Player state for {self.player_name} not found in handle_human_action.")
            self.human_action_taken = False # Allow retry if state was missing?
            return

        # Get current chip count and bet this round
        chips = player_state.get('chips', 0)
        player_bet_this_round = player_state.get('current_round_bet', 0)

        # --- Determine Final Bet Amount and Log Message ---
        # final_total_round_bet: The TOTAL amount the player will have committed this round *after* this action.
        # processed_action: The action name sent to the backend (might change "call" to "all in").
        # action_log: The message displayed in the GUI log.
        final_total_round_bet = player_bet_this_round # Default for check/fold
        action_log = action.capitalize()
        processed_action = action # Default to the button clicked

        try:
            if action == "call":
                current_bet = current_state.get('current_bet', 0)
                amount_to_call = max(0, current_bet - player_bet_this_round)
                call_chip_cost = min(amount_to_call, chips) # Can only call with chips player has
                final_total_round_bet = player_bet_this_round + call_chip_cost
                # Check if this call results in an all-in situation
                is_all_in_call = (call_chip_cost > 0 and call_chip_cost == chips)
                action_log = f"Call {call_chip_cost}" + (" (All In)" if is_all_in_call else "")
                if is_all_in_call:
                    processed_action = "all in" # Backend needs "all in" if chips run out on call
            elif action == "all in":
                final_total_round_bet = player_bet_this_round + chips
                action_log = f"All In ({chips})"
                processed_action = "all in" # Ensure backend gets "all in"
            elif action == "raise":
                # total_bet_amount was pre-validated by handle_raise_prompt
                final_total_round_bet = total_bet_amount
                raise_increment = final_total_round_bet - player_bet_this_round
                # Check if this raise results in an all-in
                is_all_in_raise = (final_total_round_bet >= player_bet_this_round + chips) # If total >= current bet + all chips
                action_log = f"Raise to {final_total_round_bet} (+{raise_increment})" + (" (All In)" if is_all_in_raise else "")
                if is_all_in_raise:
                    processed_action = "all in" # Backend needs "all in" if raise uses all chips
                    final_total_round_bet = player_bet_this_round + chips # Ensure bet amount matches all chips
            elif action == "check":
                action_log = "Check"
                # final_total_round_bet remains player_bet_this_round
            elif action == "fold":
                action_log = "Fold"
                # final_total_round_bet remains player_bet_this_round (no more added)

            # --- Log and Send to Backend ---
            self.add_log_message(f"{self.player_name}: {action_log}")
            # Call the backend method to process the action
            self.game.process_player_action(self.player_name, processed_action, final_total_round_bet)

            # --- Update UI and Trigger Next Turn ---
            self.update_ui() # Refresh UI immediately after processing
            self.root.update() # Force redraw

            # Schedule the check for the *next* player's turn after a short delay
            self.root.after(150, self.process_next_turn)

        except ValueError as e:
            # Handle potential errors from backend validation (e.g., invalid raise amount)
            messagebox.showerror("Action Error", str(e))
            self.update_ui() # Re-enable buttons if it's still player's turn
            self.human_action_taken = False # Allow action again
        except Exception as e:
            messagebox.showerror("Game Error", f"Error processing action: {e}")
            traceback.print_exc()
            # Assume game might be broken, attempt to end gracefully
            if self.game: self.game.game_over = True
            self.check_game_over() # Trigger game over check
            self.human_action_taken = False # Reset flag

    def handle_raise_prompt(self):
        """Handles the raise action: validates input or prompts player."""
        if not self.game: return # Safety check

        try:
            state = self.game.get_game_state_summary()
            player_state = state['players'].get(self.player_name)
            if not player_state: return # Cannot proceed without player state

            # Get necessary values
            chips = player_state.get('chips', 0)
            current_bet = state.get('current_bet', 0)
            player_bet_this_round = player_state.get('current_round_bet', 0)
            previous_bet = state.get('previous_bet', 0)
            big_blind = getattr(self.game, 'big_blind', 20) # Fallback if not set
            amount_to_call = max(0, current_bet - player_bet_this_round)

            # --- Calculate Minimum Legal Raise ---
            min_raise_increment = max(big_blind, current_bet - previous_bet if current_bet > previous_bet else big_blind)
            min_legal_total_bet_target = current_bet + min_raise_increment
            # Max possible total bet player can make (all-in)
            max_possible_total_bet = player_bet_this_round + chips
            # The actual minimum the player *can* raise to (cannot exceed their stack)
            min_player_can_raise_to = min(min_legal_total_bet_target, max_possible_total_bet)
            # Minimum *additional* chips needed for the minimum valid raise
            min_additional_chips_needed = 0
            if min_player_can_raise_to > player_bet_this_round: # Check if *any* raise is possible
                min_additional_chips_needed = max(1, min_player_can_raise_to - player_bet_this_round)

            # --- Check if ANY raise is possible ---
            # Must have more chips than needed to call AND afford the minimum raise increment
            can_afford_min_raise = chips >= (amount_to_call + min_additional_chips_needed) if min_additional_chips_needed > 0 else False
            if chips <= amount_to_call or not can_afford_min_raise:
                 messagebox.showinfo("Raise Info", "Not enough chips to make a valid raise.")
                 return

            # --- Get Raise Amount (from entry or dialog) ---
            target_total_bet_str = self.raise_amount_var.get()
            target_total_bet = 0

            try:
                if target_total_bet_str:
                     target_total_bet = int(target_total_bet_str)
                     # Validate amount entered in the box
                     if not (min_player_can_raise_to <= target_total_bet <= max_possible_total_bet):
                          messagebox.showwarning("Invalid Raise Amount", f"Your total bet amount must be between {min_player_can_raise_to} and {max_possible_total_bet} (All In).")
                          self.raise_amount_var.set(str(min_player_can_raise_to)) # Suggest minimum
                          return # Don't proceed with invalid amount
                else:
                    # If entry box is empty, use simpledialog to prompt
                    prompt_val = simpledialog.askinteger("Raise To",
                                                     f"Enter the TOTAL amount you want to bet this round.\n\n"
                                                     f"(Current high bet: {current_bet})\n"
                                                     f"(You have bet: {player_bet_this_round})\n"
                                                     f"------------------------------------\n"
                                                     f"Minimum Total Bet: {min_player_can_raise_to}\n"
                                                     f"Maximum Bet (All In): {max_possible_total_bet}",
                                                     parent=self.root,
                                                     initialvalue=min_player_can_raise_to, # Suggest minimum
                                                     minvalue=min_player_can_raise_to, # Enforce minimum
                                                     maxvalue=max_possible_total_bet) # Enforce maximum
                    if prompt_val is None:
                        return # User cancelled dialog

                    target_total_bet = prompt_val

                # --- Final Validation (mostly redundant for dialog, good safety check) ---
                if not (min_player_can_raise_to <= target_total_bet <= max_possible_total_bet):
                     # This case should ideally not be reached if dialog/entry validation works
                     messagebox.showwarning("Invalid Raise", f"Internal Error: Final validation failed.\nTotal bet must be between {min_player_can_raise_to} and {max_possible_total_bet}.")
                     return

                # --- Process the Validated Raise Action ---
                self.handle_human_action("raise", target_total_bet)

            except ValueError:
                # Handle non-integer input in the entry box
                messagebox.showwarning("Invalid Input","Please enter a valid whole number for the total bet amount.")
                self.raise_amount_var.set(str(min_player_can_raise_to)) # Reset entry to minimum
            except Exception as e:
                messagebox.showerror("Error", f"Error during raise input: {e}")
                traceback.print_exc()

        except Exception as e:
             messagebox.showerror("Raise Error", f"Error preparing raise prompt: {e}")
             traceback.print_exc()

    def process_next_turn(self):
        """Checks game state and decides whether to wait for human, trigger bot, or advance stage."""
        print(f"DEBUG GUI: process_next_turn triggered.")

        # --- Basic Safety Checks ---
        if not self.game:
            print("ERROR GUI: process_next_turn called but game is not initialized.")
            return
        if self.game.game_over:
            print("DEBUG GUI: process_next_turn found game is already over.")
            self.check_game_over() # Ensure game over sequence is handled
            return
        if self.game.round_over:
            print("DEBUG GUI: process_next_turn found round_over = True. Determining winner.")
            # If round is marked over, go straight to winner determination/game over check
            self.root.after(100, self.determine_winner_and_proceed)
            return

        # --- Get Current State from Backend ---
        try:
            state = self.game.get_game_state_summary()
            # Ask the backend if betting is considered finished for the current stage
            is_betting_over = self.game.is_betting_over()
            current_player_name = state.get('current_turn_player') # Who does backend say should act?
            self.current_round_name = state.get('current_stage', self.current_round_name) # Update stage display

            print(f"DEBUG GUI: process_next_turn - Backend state: Turn={current_player_name}, BettingOver={is_betting_over}, Stage={self.current_round_name}")

        except Exception as e:
             messagebox.showerror("Game State Error", f"Failed to get/process game state: {e}")
             traceback.print_exc()
             # Assume critical error, try to end game
             if self.game: self.game.game_over = True
             self.check_game_over()
             return

        # --- Decide Next Step based on State ---
        if is_betting_over:
            # If backend says betting is over, advance to the next game stage (deal cards/showdown)
            print(f"DEBUG GUI: Betting is over for {self.current_round_name}. Advancing stage.")
            self.update_ui() # Show final bets for this stage
            self.root.after(200, self.advance_game_stage) # Schedule stage advancement

        elif current_player_name is None:
             # This shouldn't happen if betting isn't over, indicates potential state issue
             print("ERROR GUI: Backend reported betting not over, but no current player specified!")
             # As a fallback, maybe try advancing stage? Could be everyone is all-in.
             self.add_log_message("Warning: Turn inconsistency detected. Attempting to advance stage.")
             self.root.after(100, self.advance_game_stage)

        elif current_player_name == self.player_name:
             # It's the human player's turn.
             print(f"DEBUG GUI: Waiting for human player ({self.player_name}) action.")
             self.human_action_taken = False # Reset flag, allow player to click
             self.update_ui() # Update UI (should enable buttons via update_action_buttons)
             # Optional log message
             # self.add_log_message(f"--- Your Turn ({self.current_round_name}) ---")

        else: # It's a bot's turn
             print(f"DEBUG GUI: Triggering action for bot: {current_player_name}")
             self.update_ui() # Update UI to show it's bot's turn (human buttons disabled)
             # Optional log message
             # self.add_log_message(f"--- {current_player_name}'s Turn ({self.current_round_name}) ---")
             self.root.update() # Ensure UI update appears visually before bot "thinks"

             # Simulate bot thinking time
             think_time = random.randint(500, 1300) # Delay 0.5 - 1.3 seconds

             # Schedule the call to the function that gets the bot's action
             self.root.after(think_time, self.get_bot_action, current_player_name)

    def get_bot_action(self, bot_name):
        """Gets and processes the specified bot's action from the game logic."""
        # --- Basic Safety Checks ---
        if not self.game or self.game.round_over or self.game.game_over:
            print(f"DEBUG GUI: get_bot_action for {bot_name} skipped, round/game over.")
            return

        # Optional: Verify backend agrees it's this bot's turn
        try:
            backend_turn = self.game.get_game_state_summary().get('current_turn_player')
            if backend_turn != bot_name:
                print(f"ERROR GUI: get_bot_action called for {bot_name} but backend turn is {backend_turn}. Triggering next turn check.")
                # If turn mismatch, don't get bot action, just re-trigger turn check
                self.root.after(50, self.process_next_turn)
                return
        except Exception as e:
             print(f"ERROR GUI: Failed to verify turn with backend in get_bot_action: {e}")
             # Proceed cautiously if check fails

        # --- Get and Process Bot Action ---
        try:
            # Call the backend method designed for the GUI to get bot's decision
            action, total_bet_amount = self.game.get_bot_action_gui(bot_name)

            # Get bot's state for logging calculations
            player_state = self.game.players.get(bot_name)
            chips = player_state.get('chips', 0) if player_state else 0
            player_bet_this_round = player_state.get('current_round_bet', 0) if player_state else 0

            # --- Determine Log Message and Final Processed Action ---
            action_log = action.capitalize()
            processed_action = action # Action sent to backend
            final_total_round_bet = 0 # Total bet this round after action

            # Refine log message and determine if action results in "all in"
            if action == "call":
                current_bet = self.game.current_bet # Get current high bet
                amount_to_call = max(0, current_bet - player_bet_this_round)
                call_chip_cost = min(amount_to_call, chips) if amount_to_call > 0 else 0
                is_all_in = (call_chip_cost > 0 and call_chip_cost == chips)
                action_log = f"Call {call_chip_cost}" + (" (All In)" if is_all_in else "")
                if is_all_in: processed_action = "all in"
                final_total_round_bet = player_bet_this_round + call_chip_cost
            elif action == "raise":
                # total_bet_amount is provided by get_bot_action_gui
                raise_increment = total_bet_amount - player_bet_this_round
                is_all_in = (total_bet_amount >= player_bet_this_round + chips) # If total bet >= current bet + all chips
                action_log = f"Raise to {total_bet_amount} (+{raise_increment})" + (" (All In)" if is_all_in else "")
                if is_all_in:
                    processed_action = "all in"
                    final_total_round_bet = player_bet_this_round + chips # Actual bet is capped by chips
                else:
                    final_total_round_bet = total_bet_amount
            elif action == "all in":
                 action_log = f"All In ({chips})"
                 processed_action = "all in"
                 final_total_round_bet = player_bet_this_round + chips
            elif action == "check":
                 action_log = "Check"
                 final_total_round_bet = player_bet_this_round
            elif action == "fold":
                 action_log = "Fold"
                 final_total_round_bet = player_bet_this_round # Bet doesn't change

            # --- Log, Process Action, Update UI, Trigger Next ---
            self.add_log_message(f"{bot_name}: {action_log}")
            # Send the processed action and final bet amount to the backend
            self.game.process_player_action(bot_name, processed_action, final_total_round_bet)
            self.update_ui() # Refresh UI
            self.root.update() # Force redraw

            # Schedule the check for the *next* player's turn
            self.root.after(150, self.process_next_turn)

        except Exception as e: # Catch errors during bot action processing
             messagebox.showerror("Bot Action Error", f"Error during {bot_name}'s turn: {e}")
             traceback.print_exc()
             # Attempt to fold the bot gracefully on error
             try:
                 self.add_log_message(f"Error during {bot_name}'s turn, folding.")
                 if self.game:
                     self.game.process_player_action(bot_name, "fold", 0) # Use 0 bet for fold
                 self.update_ui()
                 # Still trigger next turn check after folding
                 self.root.after(150, self.process_next_turn)
             except Exception as fold_e:
                 # If even folding fails, declare game over
                 print(f"ERROR GUI: Failed to fold bot {bot_name} after error: {fold_e}")
                 if self.game: self.game.game_over = True
                 self.check_game_over() # Trigger game over sequence

    def advance_game_stage(self):
         """Tells the game logic to advance (deal flop/turn/river/showdown) and updates UI accordingly."""
         print(f"DEBUG GUI: advance_game_stage called. Current stage was: {self.current_round_name}")
         if not self.game: return
         if self.game.game_over:
              self.check_game_over()
              return

         # --- Check for premature round end (only 1 active player) ---
         # This might happen if everyone else folded during the previous betting round.
         try:
            state = self.game.get_game_state_summary()
            active_players = [p for p in state['players'].values() if not p.get('folded') and not p.get('all_in')] # Check active AND not all-in
            all_in_players = [p for p in state['players'].values() if p.get('all_in')]
            # If only 0 or 1 player can still bet, the round should end (or skip to showdown)
            should_end_early = len(active_players) <= 1

            # Also consider case where multiple are all-in, but no one else can bet
            if not active_players and len(all_in_players) > 1:
                 should_end_early = True # Force showdown if only all-in players remain

            if should_end_early and not self.game.round_over:
                  # If backend hasn't marked round over yet, do it now based on GUI check
                  self.game.round_over = True
                  self.add_log_message("\n--- Round End (Betting concluded / Only one active player) ---")
                  print("DEBUG GUI: advance_game_stage -> Round ending early.")
                  self.update_ui(show_bot_cards=True) # Reveal cards if round ends here
                  # Proceed to determine winner / check game over status
                  self.root.after(100, self.determine_winner_and_proceed)
                  return
         except Exception as e:
             print(f"Error checking for premature round end: {e}")
             # Continue cautiously

         # --- Ask Backend to Advance Stage ---
         try:
             # This method in MatchManager_GUI should handle dealing cards and updating its state
             next_stage = self.game.advance_to_next_stage()
             print(f"DEBUG GUI: game.advance_to_next_stage() returned stage: {next_stage}")
             if self.game: # Check game object still valid
                self.current_round_name = self.game.current_stage # Get updated stage name
         except AttributeError:
             messagebox.showerror("Game Error", "Game logic missing 'advance_to_next_stage' method.")
             if self.game: self.game.game_over = True
             self.check_game_over(); return
         except Exception as e:
              messagebox.showerror("Stage Error", f"Error advancing game stage logic: {e}")
              traceback.print_exc()
              if self.game: self.game.game_over = True
              self.check_game_over(); return

         # --- Process the Result ---
         if next_stage == "showdown":
             self.add_log_message("\n--- Dealing Showdown ---")
             self.update_ui(show_bot_cards=True) # Reveal all cards for showdown
             self.root.update() # Ensure cards are visible
             # Proceed to determine the winner after a short delay
             self.root.after(500, self.determine_winner_and_proceed) # Longer delay before winner

         elif next_stage: # "flop", "turn", or "river" successfully dealt
             self.add_log_message(f"\n--- Dealing {next_stage.capitalize()} ---")

             # --- Start the Betting Round for the New Stage ---
             try:
                # This backend method should reset betting state and determine who starts
                round_info = self.game.start_next_betting_round()
                gui_turn_order = round_info.get('turn_order', []) # Get turn order for this stage
                gui_start_index = round_info.get('start_index', -1) # Get who starts betting
                print(f"DEBUG GUI: New betting round ({next_stage}). Turn order: {gui_turn_order}, Start index: {gui_start_index}")

                # Check if betting is skipped (e.g., only one player left or all others all-in)
                if not gui_turn_order or gui_start_index < 0:
                     self.add_log_message(f"(Betting skipped for {next_stage})")
                     print(f"DEBUG GUI: Betting skipped for {next_stage} (no actors or all-in).")
                     self.update_ui() # Update UI to show new community cards
                     self.root.after(500, self.advance_game_stage) # Advance again quickly
                     return # Skip calling process_next_turn

             except AttributeError:
                 messagebox.showerror("Game Error", "Game logic missing 'start_next_betting_round' method.")
                 if self.game: self.game.game_over = True; self.check_game_over(); return
             except Exception as e:
                 messagebox.showerror("Betting Round Error", f"Error starting betting round for {next_stage}: {e}")
                 traceback.print_exc()
                 if self.game: self.game.game_over = True; self.check_game_over(); return

             # --- Betting Round Starts ---
             self.update_ui() # Show new community cards
             self.root.update() # Force redraw

             # Start the betting process for this new stage
             print(f"DEBUG GUI: Triggering process_next_turn for new stage: {next_stage}")
             self.root.after(500, self.process_next_turn) # Delay before first action prompt

         else:
              # Stage advancement failed or returned None/False (might mean round ended)
              print(f"Warning GUI: advance_to_next_stage returned {next_stage}. Checking round/game state.")
              if self.game and not self.game.round_over:
                  # If backend didn't mark round over, perhaps GUI should trigger winner check
                   self.add_log_message("Warning: Stage advancement ended unexpectedly. Determining winner.")
                   self.root.after(100, self.determine_winner_and_proceed)
              elif self.game and self.game.round_over:
                   # Round is already over, just check game over status
                   self.check_game_over()
              else: # Game object missing
                   print("ERROR GUI: Game object missing after failed stage advance.")


    def determine_winner_and_proceed(self):
        """Calls backend to determine winner, displays info, and checks game over."""
        print("DEBUG GUI: determine_winner_and_proceed called.")
        if not self.game: return

        try:
            # Get winner information (including evaluated hands) from backend
            winner_info = self.game.determine_winner_gui()
            # Display the winner(s) and hand details in the log
            self.display_winner(winner_info)
        except AttributeError:
            messagebox.showerror("Game Error", "Game logic missing 'determine_winner_gui' method.")
            # Assume fatal if core logic missing
            if self.game: self.game.game_over = True
        except Exception as e:
            self.add_log_message(f"Error determining winner: {e}")
            traceback.print_exc()
            # Optionally set game over on error, or try to continue
            # if self.game: self.game.game_over = True

        # ALWAYS check game over status after determining the round winner
        # Use a slight delay to allow user to read the winner message
        self.root.after(1500, self.check_game_over) # Delay before checking game end

    def display_winner(self, winner_info):
        """Displays detailed winner information and hand results in the log area."""
        if not winner_info:
            self.add_log_message("\nError: Winner information missing.")
            return

        winners = winner_info.get('winners', [])
        pot_before_distribution = winner_info.get('pot', 0) # Pot shown should be before payout
        details = winner_info.get('details', {}) # Hand evaluation details per player

        # --- Log Hand Results ---
        if details:
            self.add_log_message("--- Hand Results ---")
            # Get latest state AFTER pot distribution if possible (depends on when determine_winner runs)
            current_state = self.game.get_game_state_summary()
            player_states = current_state.get('players', {})

            # Try to display in original player order for consistency
            player_order = list(self.game.players.keys()) if hasattr(self.game, 'players') else list(details.keys())
            displayed_players = set() # Keep track of who we've logged

            for name in player_order:
                 if name in details:
                     detail = details.get(name)
                     player_state = player_states.get(name) # Get potentially updated state (chips/hearts)
                     if detail and player_state:
                          # Get hole cards (prefer from details, fallback to current state)
                          hole_cards = detail.get('hole_cards', player_state.get('cards', []))
                          hole_cards_str = " ".join(hole_cards) if hole_cards else "?? ??"
                          hand_type = detail.get('type', 'N/A')
                          best_5_cards = detail.get('hand', []) # The best 5 cards making the hand
                          best_5_str = " ".join(best_5_cards) if best_5_cards else ""

                          # Construct log line based on player status and hand
                          log_line = f"  {name}: "
                          if player_state.get('folded'):
                              log_line += f"Folded ({hole_cards_str})"
                          elif hand_type == 'Default (Others Folded)':
                              log_line += f"Wins by default ({hole_cards_str})"
                          elif hand_type in ['Mucked/Invalid', 'Eval Error', 'Eval Exception', 'N/A']:
                               # Show problematic hands or unknown status
                               log_line += f"{hand_type} ({hole_cards_str})"
                          else: # Valid hand evaluated
                               log_line += f"{hand_type} ({hole_cards_str}"
                               if best_5_str: log_line += f" -> {best_5_str}" # Show the best 5-card hand
                               log_line += ")"

                          self.add_log_message(log_line)
                          displayed_players.add(name) # Mark as displayed

            # Display any players from details missed in the initial loop (safety)
            for name, detail in details.items():
                 if name not in displayed_players:
                     player_state = player_states.get(name)
                     status = detail.get('type', 'Unknown Status')
                     hole_cards_str = " ".join(detail.get('hole_cards', [])) if detail.get('hole_cards') else "??"
                     self.add_log_message(f"  (Other) {name}: ({hole_cards_str}) - {status}")

        # --- Log Winner Message ---
        # Use distributed amount if backend provides it, else use original pot
        distributed_pot = winner_info.get('distributed_pot', pot_before_distribution)
        if len(winners) == 1:
             winner = winners[0]
             win_msg = f"\n---> {winner} wins the pot of {distributed_pot}!"
             self.add_log_message(win_msg)
        elif len(winners) > 1:
             win_amount = winner_info.get('win_amount', 0) # Amount per winner if provided
             win_msg = f"\n---> Split pot ({distributed_pot}) between: {', '.join(winners)}"
             if win_amount > 0:
                 win_msg += f" ({win_amount} each)"
             self.add_log_message(win_msg)
        else: # No winners declared? Should only happen if pot was 0 or error.
             if distributed_pot > 0:
                 self.add_log_message(f"\n--- No winner declared for pot ({distributed_pot}). Pot remains? Check logic. ---")
             else:
                 self.add_log_message("\n--- Round concludes (No contest / Pot = 0). ---")

        # --- Log Heart Changes ---
        # Compare hearts before/after the round end processing
        final_human_state = self.game.get_game_state_summary()['players'].get(self.player_name)
        if final_human_state:
             start_hearts = final_human_state.get('start_round_hearts') # Hearts at round start
             current_hearts = final_human_state.get('hearts') # Hearts now

             # Check if backend explicitly flagged a heart exchange this cycle
             # (Backend would need to set/clear this flag, e.g., self.game._human_exchanged_heart_flag = True)
             if getattr(self.game, '_human_exchanged_heart_flag', False):
                 self.add_log_message(f"---> {self.player_name} exchanged a heart for chips! ({current_hearts} left) <---")
                 self.game._human_exchanged_heart_flag = False # Reset the flag after logging

             # Log heart loss only if hearts decreased *and* no exchange was just logged
             elif start_hearts is not None and current_hearts < start_hearts :
                  heart_loss = start_hearts - current_hearts
                  plural = "s" if heart_loss > 1 else ""
                  self.add_log_message(f"---> {self.player_name} lost {heart_loss} heart{plural}! ({current_hearts} left) <---")

        # Update UI one last time for the round to show final chip/heart counts
        self.update_ui(show_bot_cards=True) # Show all cards at end of round display
        self.root.update() # Force draw

    def prepare_for_next_round_or_end(self):
        """Adds 'Start Next Round' button if game is not over, otherwise does nothing."""
        print("DEBUG GUI: prepare_for_next_round_or_end called.")
        if not self.game:
             print("DEBUG GUI: prepare... -> game object is None.")
             return
        # Check the game over flag *after* winner determination
        if self.game.game_over:
             print("DEBUG GUI: prepare... -> game is over. No 'Next Round' button.")
             # Could potentially add a "Return to Menu" button here if desired
             return

        # --- Clean up previous button if it exists ---
        if hasattr(self, 'next_round_button') and self.next_round_button:
            try:
                # Check if the widget actually exists before trying to destroy
                if self.next_round_button.winfo_exists():
                     self.next_round_button.destroy()
                # Delete the attribute reference for safety
                delattr(self, 'next_round_button')
            except (tk.TclError, AttributeError, NameError):
                pass # Ignore errors if already gone

        # --- Add the 'Start Next Round' button ---
        # Place it below the pot info area
        self.next_round_button = ttk.Button(self.game_frame, text="Start Next Round", command=self.click_next_round)
        self.next_round_button.grid(row=1, column=1, pady=10, sticky="s", columnspan=1) # Place below pot/bet info
        print("DEBUG GUI: prepare... -> Added 'Start Next Round' button.")

    def click_next_round(self):
        """Handles the 'Start Next Round' button click."""
        print("DEBUG GUI: click_next_round called.")

        # --- Remove the button ---
        if hasattr(self, 'next_round_button') and self.next_round_button:
            try:
                 if self.next_round_button.winfo_exists():
                      self.next_round_button.destroy()
                 delattr(self, 'next_round_button')
            except (tk.TclError, AttributeError, NameError):
                pass # Ignore errors

        # --- Start the next round if game logic exists and isn't over ---
        if self.game and not self.game.game_over:
            # Reset round-specific UI elements (like community cards)
            for lbl in self.community_card_labels:
                 if self.card_back_image:
                      lbl.config(image=self.card_back_image)
                      lbl.image = self.card_back_image
                 else: # Fallback if card back failed to load
                      lbl.config(image='')
                      lbl.image = None
            self.current_round_name = "" # Reset stage name display
            # Call the method to start the new round logic
            self.start_new_round()
        elif self.game and self.game.game_over:
             # Should not happen if button wasn't shown, but safety check
             messagebox.showinfo("Game Over", "The game has already ended.")
        else:
             messagebox.showerror("Error", "Game logic is missing or not initialized.")

    def check_game_over(self):
        """Checks game over status with backend and triggers appropriate UI action."""
        print("DEBUG GUI: check_game_over called.")
        if not self.game: return

        # Ensure UI shows final state of the round clearly before checking game end
        try:
            self.update_ui(show_bot_cards=True) # Show all cards
            self.root.update_idletasks() # Process pending UI events
        except tk.TclError:
            # Window might be closing, ignore UI update error
            pass

        is_over = False
        message = "Game ended unexpectedly."
        reason = "unknown"

        # --- Get Game Over Status from Backend ---
        try:
            is_over, message, reason = self.game.check_game_over_status()
            print(f"DEBUG GUI: game.check_game_over_status() -> is_over={is_over}, reason='{reason}', message='{message}'")
        except AttributeError:
             messagebox.showerror("Game Error", "Game logic missing 'check_game_over_status' method.")
             is_over, message, reason = True, "Game logic error", "internal"
             # Assume fatal error, ensure flags are set
             if self.game: self.game.game_over = True
             if self.game and not hasattr(self.game, 'game_over_handled'): self.game.game_over_handled = False
        except Exception as e:
             messagebox.showerror("Game Error", f"Error checking game over status: {e}")
             traceback.print_exc()
             is_over, message, reason = True, "Game logic error", "internal"
             if self.game: self.game.game_over = True
             if self.game and not hasattr(self.game, 'game_over_handled'): self.game.game_over_handled = False

        # --- Process Game Over State (Only Once) ---
        # Use a flag within the game logic object to prevent multiple triggers
        if is_over and not getattr(self.game, 'game_over_handled', False):
            if self.game:
                 self.game.game_over = True # Ensure main flag is definitely set
                 self.game.game_over_handled = True # Mark as handled

            print("DEBUG GUI: Game over condition met and not handled yet.")
            self.disable_all_buttons() # Disable actions permanently

            # Ensure 'Next Round' button is removed if it was somehow present
            if hasattr(self, 'next_round_button') and self.next_round_button:
                 try:
                      if self.next_round_button.winfo_exists(): self.next_round_button.destroy()
                      if hasattr(self, 'next_round_button'): delattr(self, 'next_round_button')
                 except (tk.TclError, AttributeError, NameError): pass

            # Log the final game over message
            log_message = message or "The game has ended." # Use provided message or default
            self.add_log_message(f"\n{'='*15} {log_message} {'='*15}")

            # --- Trigger Specific Ending Based on Reason ---
            if reason == "hearts" or reason == "busted": # Human lost all hearts or busted final hand
                self.add_log_message("--- Your deal with the Devil concludes... ---")
                # Schedule the dramatic ending sequence after a delay
                self.root.after(1500, self.show_game_over_sequence)
            elif reason == "bot_bust" or reason == "chips": # Player won (bots busted or player last one with chips)
                 messagebox.showinfo("Game Over - You Win!", log_message)
                 self.add_log_message("--- YOU HAVE DEFIED THE DEVIL! (For now...) ---")
                 # Consider adding a "Return to Menu" button here automatically
            else: # Other reasons (e.g., internal error, no chips left)
                messagebox.showinfo("Game Over", log_message)
                self.add_log_message("--- THE HOUSE ALWAYS WINS... EVENTUALLY ---")
                # Consider adding "Return to Menu" here too

        elif not is_over and getattr(self.game, 'round_over', False):
             # Round ended, but game continues -> Show next round button
             print("DEBUG GUI: check_game_over -> Round over, game continues. Calling prepare_for_next_round.")
             self.prepare_for_next_round_or_end()
        elif not is_over and not getattr(self.game, 'round_over', False):
            # Game and round are still in progress (shouldn't usually reach here directly after winner display)
            print("DEBUG GUI: check_game_over -> Game/Round continue (unexpected state?).")
        # else: Game is over and was already handled in a previous call


    def show_game_over_sequence(self):
        """Displays the ending script in a dedicated frame when hearts run out."""
        if self.ending_frame and self.ending_frame.winfo_exists():
            print("DEBUG GUI: Ending sequence already showing.")
            return # Prevent multiple sequences

        print("DEBUG GUI: Starting game over sequence.")
        # --- Hide Game UI ---
        if self.game_frame.winfo_ismapped(): self.game_frame.pack_forget()
        if self.log_frame.winfo_ismapped(): self.log_frame.pack_forget()

        # --- Create Ending Frame ---
        self.ending_frame = tk.Frame(self.root, bg="black")
        self.ending_frame.pack(fill=tk.BOTH, expand=True)

        # --- Create Text Widget for Script ---
        self.ending_text_widget = Text(self.ending_frame, bg="black", fg="white", wrap=tk.WORD,
                                       padx=50, pady=50, bd=0, highlightthickness=0,
                                       font=self.SEQ_FONT_NORMAL)
        self.ending_text_widget.pack(fill=tk.BOTH, expand=True)
        self.ending_text_widget.config(state=tk.DISABLED) # Make read-only

        # --- Configure Text Tags for Formatting ---
        self.ending_text_widget.tag_configure("devil", foreground=self.SEQ_COLOR_DEVIL, font=self.SEQ_FONT_DEVIL)
        self.ending_text_widget.tag_configure("narrator", foreground=self.SEQ_COLOR_NARRATOR, font=self.SEQ_FONT_NORMAL)
        self.ending_text_widget.tag_configure("man", foreground=self.SEQ_COLOR_MAN, font=self.SEQ_FONT_NORMAL)
        self.ending_text_widget.tag_configure("center", justify='center')
        self.ending_text_widget.tag_configure("prompt", foreground=self.SEQ_COLOR_DEFAULT, font=self.SEQ_FONT_NORMAL, justify='center')

        # --- Game Over Script Lines (text, tag, delay_ms) ---
        self.ending_script_lines = [
            ("The Devil: \"Your time is come.\"", "devil", 2500),
            ("", None, 500),
            ("The crimson glow fades from the cards.", "narrator", 2000),
            ("You feel a chilling emptiness, a price paid.", "narrator", 2500),
            ("", None, 500),
            ("Your reflection shimmers, decades stolen in moments.", "narrator", 2500),
            ("The chips turn to dust in your trembling hands.", "narrator", 2000),
            ("", None, 500),
            ("The Devil: \"A soul for a chance... a poor trade, wouldn't you say?\"", "devil", 3500),
            ("The Devil: \"But don't worry... there are always more eager players.\"", "devil", 3000),
            ("", None, 1000),
            ("(The felt table awaits its next victim.)", "narrator", 2500),
            ("", None, 1000),
            ("The Devil: \"Perhaps... you'll try again?\"", "devil", 3000),
            ("", None, 1000),
            # Anti-gambling hotline message (Example - adjust as needed)
            ("Gambling Problem? Call 1-800-GAMBLER", "prompt", 10), # Use a relevant hotline #
            ("", None, 1000),
            ("\n\n(Press any key or click to close the table)", "prompt", 0) # Prompt to close
        ]

        # --- Start Displaying Lines ---
        self.ending_current_line = 0
        # Clear any previous pending job ID
        if self.ending_after_id:
             try: self.root.after_cancel(self.ending_after_id)
             except ValueError: pass
             self.ending_after_id = None
        # Start the sequence
        self._display_next_ending_line()

        # --- Bind Events to Close Window ---
        # Bind to root, frame, and text widget for broader capture
        self.root.bind("<KeyPress>", self._end_game_sequence_key)
        self.ending_frame.bind("<Button-1>", self._end_game_sequence_key)
        self.ending_text_widget.bind("<Button-1>", self._end_game_sequence_key)

    def _display_next_ending_line(self):
        """Internal method to display script lines sequentially with delays."""
        # Check if widgets still exist
        if not self.ending_text_widget or not self.ending_frame or not self.ending_frame.winfo_exists():
            print("DEBUG GUI: Ending sequence widgets destroyed, stopping display.")
            return

        # Stop if all lines shown
        if self.ending_current_line >= len(self.ending_script_lines):
            return

        # Get current line data
        line, tag, delay_ms = self.ending_script_lines[self.ending_current_line]

        try:
            # Insert the line with its tag
            self.ending_text_widget.config(state=tk.NORMAL)
            if tag:
                self.ending_text_widget.insert(tk.END, line + "\n", tag)
            else:
                self.ending_text_widget.insert(tk.END, line + "\n")
            self.ending_text_widget.see(tk.END) # Scroll to the end
            self.ending_text_widget.config(state=tk.DISABLED)
        except tk.TclError:
            print("Error: Ending text widget likely destroyed during insert.")
            return # Stop if widget gone

        # Increment line counter
        self.ending_current_line += 1

        # Schedule the next line display if there are more lines and delay > 0
        if delay_ms > 0 and self.ending_current_line < len(self.ending_script_lines):
            # Cancel previous job if any
            if self.ending_after_id:
                 try: self.root.after_cancel(self.ending_after_id)
                 except ValueError: pass
            # Schedule the next call
            self.ending_after_id = self.root.after(delay_ms, self._display_next_ending_line)
        elif self.ending_current_line >= len(self.ending_script_lines):
             # All lines shown, ensure last line (prompt) is visible
             try:
                 if self.ending_text_widget.winfo_exists(): self.ending_text_widget.see(tk.END)
             except tk.TclError: pass
             self.ending_after_id = None # No more scheduled calls

    def _end_game_sequence_key(self, event=None):
        """Handles key press or click during the ending sequence to close the Poker window."""
        print("DEBUG GUI: _end_game_sequence_key triggered.")

        # Cancel any pending text display jobs
        if self.ending_after_id:
            try:
                self.root.after_cancel(self.ending_after_id)
                self.ending_after_id = None
            except ValueError:
                pass # Ignore error if already cancelled

        # --- Unbind events to prevent multiple calls ---
        try:
            self.root.unbind("<KeyPress>")
            # Check if frames/widgets exist before unbinding
            if self.ending_frame and self.ending_frame.winfo_exists():
                 self.ending_frame.unbind("<Button-1>")
            if self.ending_text_widget and self.ending_text_widget.winfo_exists():
                 self.ending_text_widget.unbind("<Button-1>")
        except tk.TclError:
            print("Warning: TclError during ending sequence unbind (window might be closing).")
            pass

        # --- Close THIS Toplevel window ---
        # This action should trigger the `on_poker_close` handler set up in `MainMenu`.
        try:
            print("DEBUG GUI: Destroying PokerGUI Toplevel window.")
            self.root.destroy()
        except tk.TclError:
            print("Warning: TclError destroying PokerGUI window (already destroying?).")
            pass # Ignore error if window is already gone

    def _return_to_menu(self):
        """Handles the 'Return to Menu' button click: Confirms and closes this window."""
        # Ask for confirmation
        if messagebox.askokcancel("Menu", "Leave the current game and return to the main menu?\nGame progress will be lost."):
            self.add_log_message("--- Returning to Main Menu ---")
            try:
                # --- Cancel Pending Jobs ---
                # Cancel any 'after' jobs scheduled specifically for this Toplevel window
                widget = self.root # Use the Toplevel window as the widget context
                after_ids = widget.tk.call('after', 'info') # Get IDs scheduled for this widget
                for after_id in after_ids:
                    try:
                         widget.after_cancel(after_id) # Attempt cancellation
                    except tk.TclError:
                         pass # Ignore error if job already ran or ID is invalid

                # --- Destroy the Toplevel Window ---
                # This is the crucial step. Closing this window signals back to MainMenu.
                print("DEBUG GUI: Destroying PokerGUI window via Return to Menu button.")
                self.root.destroy()

            except tk.TclError:
                # Ignore errors if the window is already in the process of being destroyed
                print("Warning: TclError during _return_to_menu cleanup (window likely closing).")
                pass
            except Exception as e:
                 print(f"Error during _return_to_menu cleanup: {e}")
                 traceback.print_exc()
                 # Fallback: Try destroying window even if cleanup failed
                 try: self.root.destroy()
                 except tk.TclError: pass

# --- Main Execution Block (for standalone testing) ---
if __name__ == "__main__":
    print("Running PokerGUI directly for testing...")
    # Create a main Tkinter window ONLY for standalone testing
    main_root = tk.Tk()
    # Instantiate the PokerGUI using the main root (acting as the Toplevel)
    app = PokerGUI(main_root)
    # When running standalone, the 'X' button should probably just quit
    # We can reuse _return_to_menu which now just closes the window.
    main_root.protocol("WM_DELETE_WINDOW", app._return_to_menu)
    # Start the Tkinter event loop
    main_root.mainloop()
    print("PokerGUI standalone test finished.")

# --- END OF FILE PokerGUI.py ---