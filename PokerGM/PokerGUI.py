import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, font, Text
import time
import random
import os
import traceback # Import traceback for detailed error printing
from PIL import Image, ImageTk
import tkinter.messagebox
from MatchManager_GUI import PokerGame, INITIAL_HEARTS, HEART_CHIP_EXCHANGE_AMOUNT
from BotPlayer import BotPlayer
from HandEvaluator import HandEvaluator # HandRank not directly used in GUI, but good to have evaluator
from Deck import Deck
# --- Attempt to import Pillow (PIL) ---

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
    SEQ_COLOR_MAN = "#AAAAFF" # Example color
    SEQ_COLOR_DEFAULT = "#FFFFFF"
    STARTING_CHIPS = 1000 # Default starting chips

    # MODIFIED __init__ to accept callback
    def __init__(self, root, on_close_callback=None): # Add callback parameter, default to None
        """Initializes the Poker GUI within the provided Tkinter root (Toplevel window)."""
        self.root = root # This root is the Toplevel window passed from MainMenu
        self.on_close_callback = on_close_callback # Store the callback function

        self.root.title("Poker Game - Devil's Deal")
        self.root.geometry("1280x800") # Set initial size
        self.root.configure(bg=self.TABLE_GREEN) # Set root background

        self.image_dir = "cards" # Subdirectory for card images
        self.card_images = {} # Dictionary to hold loaded card PhotoImage objects
        self.card_back_image = None # To hold the loaded card back PhotoImage
        self._load_card_images() # Load images immediately

        # --- Font Definitions ---
        try:
            self.status_font = font.Font(family="Arial", size=12)
            self.heart_font = font.Font(family="Arial", size=14, weight="bold")
            self.log_font = font.Font(family="Consolas", size=9) # Monospaced font for log
            self.button_font = font.Font(family="Arial", size=10)
            self.labelframe_font = font.Font(family="Arial", size=11, weight="bold")
        except tk.TclError: # Fallback if system fonts aren't found
            print("Warning: Arial/Consolas font not found, using default.")
            self.status_font = font.Font(size=12)
            self.heart_font = font.Font(size=14, weight="bold")
            self.log_font = font.Font(size=9)
            self.button_font = font.Font(size=10)
            self.labelframe_font = font.Font(size=11, weight="bold")

        # --- Game State Variables ---
        self.game = None # Will hold the PokerGame instance from MatchManager_GUI
        self.player_name = "Player" # Default player name
        self.bot_count = 1 # Default bot count
        self.bot_difficulty = "easy" # Default bot difficulty
        self.human_action_taken = False # Flag to prevent duplicate actions on clicks

        # --- UI Frames ---
        # Setup Frame (for initial options)
        self.setup_frame = ttk.Frame(root, padding="20")
        self.setup_frame.configure(style="Setup.TFrame") # Use a specific style if needed

        # Game Frame (main play area)
        self.game_frame = ttk.Frame(root, padding="10")
        self.game_frame.configure(style="Game.TFrame") # Use game style

        # Log Frame (at the bottom)
        self.log_frame = ttk.Frame(root, padding="5")
        # Widgets for ending sequence (created later if needed)
        self.ending_frame = None
        self.ending_text_widget = None
        self.ending_script_lines = []
        self.ending_current_line = 0
        self.ending_after_id = None # ID for scheduled ending text display

        # --- Style Configuration (using ttk for better appearance) ---
        self.style = ttk.Style()
        self.style.theme_use('clam') # Use a theme that allows more customization

        # Frame styles
        self.style.configure("Setup.TFrame", background="#333333") # Dark grey for setup
        self.style.configure("Game.TFrame", background=self.TABLE_GREEN)

        # Label styles
        self.style.configure("TLabel", background=self.TABLE_GREEN, foreground="white", font=self.status_font) # Default label
        self.style.configure("Setup.TLabel", background="#333333", foreground="white", font=self.status_font)
        self.style.configure("GreenBG.TLabel", background=self.TABLE_GREEN, foreground="white", font=self.status_font)
        self.style.configure("Hearts.TLabel", background=self.TABLE_GREEN, foreground="#FF5555", font=self.heart_font) # Brighter red for hearts

        # Button styles
        self.style.configure("TButton", font=self.button_font, padding=5)
        self.style.map("TButton",
                       foreground=[('active', 'white'), ('disabled', '#AAAAAA')],
                       background=[('active', '#FF4444'), ('!disabled', '#555555')],
                       relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        self.style.configure("Action.TButton", font=self.button_font, padding=(10, 5)) # Specific style for action buttons

        # LabelFrame style
        self.style.configure("GreenBG.TLabelframe", background=self.TABLE_GREEN, bordercolor="#CCCCCC")
        self.style.configure("GreenBG.TLabelframe.Label", background=self.TABLE_GREEN, foreground="white", font=self.labelframe_font)

        # Entry style
        self.style.configure("TEntry", foreground="black", background="white", padding=3)

        # --- Log Area Setup ---
        self.log_text = Text(self.log_frame, height=8, width=110, wrap=tk.WORD, font=self.log_font,
                             relief=tk.SUNKEN, borderwidth=1, state=tk.DISABLED,
                             bg="#282828", fg="#E0E0E0", insertbackground="white") # Darker log, bright text
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
        self.setup_frame.pack(fill=tk.BOTH, expand=True) # Show setup frame first

        # Create the widgets for setup and game screens (game widgets are hidden initially)
        self._create_setup_widgets()
        self._create_game_widgets() # Create game widgets but don't pack game_frame yet

        # Handle window close ('X' button) - Now handled by MainMenu passing callback


    def _load_card_images(self):
        """Loads and resizes card images from the 'cards' directory."""
        if not os.path.isdir(self.image_dir):
            messagebox.showerror("Error", f"Image directory '{self.image_dir}' not found.\nPlease ensure a 'cards' subfolder exists with card images.")
            if self.root.winfo_exists(): self.root.quit() # Cannot proceed without images
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
                    print(f"Warning: Invalid rank/suit shorthand combination: {rank_short}{suit_short}")
                    continue # Skip if shorthand isn't recognized

                # Assume JPG format for now, consider adding PNG fallback?
                filename = f"{rank_file}_of_{suit_file}.jpg"
                file_path = os.path.join(self.image_dir, filename)

                try:
                    img = Image.open(file_path)
                    img = img.resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS) # High-quality resize
                    self.card_images[card_shorthand] = ImageTk.PhotoImage(img)
                    loaded_count += 1
                except FileNotFoundError:
                    print(f"Warning: Image file not found: {file_path}")
                    if filename not in missing_files: missing_files.append(filename)
                    self.card_images[card_shorthand] = None # Store None placeholder
                except Exception as e:
                    print(f"Warning: Failed to load/resize image {file_path}: {e}")
                    if filename not in missing_files: missing_files.append(filename)
                    self.card_images[card_shorthand] = None

        # Load card back
        card_back_path = os.path.join(self.image_dir, "card_back.jpg")
        try:
            img = Image.open(card_back_path)
            img = img.resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS)
            self.card_back_image = ImageTk.PhotoImage(img)
            loaded_count += 1
        except FileNotFoundError:
            print(f"ERROR: Card back image file not found: {card_back_path}")
            self.card_back_image = None
            if "card_back.jpg" not in missing_files: missing_files.append("card_back.jpg")
        except Exception as e:
            print(f"ERROR: Failed to load/resize card back image {card_back_path}: {e}")
            self.card_back_image = None
            if "card_back.jpg" not in missing_files: missing_files.append("card_back.jpg")

        print(f"Loaded {loaded_count}/{expected_count} card images.")
        if missing_files:
             warning_msg = "Failed to load the following card images:\n"
             warning_msg += "\n".join(f"- {fname}" for fname in sorted(missing_files))
             warning_msg += "\n\nPlaceholders (or blank areas) will be used. Check console and 'cards' folder."
             messagebox.showwarning("Image Load Warning", warning_msg)


    def _create_setup_widgets(self):
        """Creates the widgets for the initial game setup screen."""
        # Configure grid for centering in setup frame
        self.setup_frame.columnconfigure(0, weight=1)
        self.setup_frame.columnconfigure(2, weight=1) # Add padding columns

        # Title
        title_label = ttk.Label(self.setup_frame, text="Poker Setup - Devil's Deal", font=("Arial", 20, "bold"), style="Setup.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=(20, 30))

        # Use a sub-frame for options alignment
        options_frame = ttk.Frame(self.setup_frame, style="Setup.TFrame")
        options_frame.grid(row=1, column=1, sticky="ew")

        # Player Name Input
        ttk.Label(options_frame, text="Your Name:", style="Setup.TLabel").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.name_entry = ttk.Entry(options_frame, width=30, font=self.status_font)
        self.name_entry.insert(0, self.player_name) # Pre-fill with default
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Bot Count Selection
        ttk.Label(options_frame, text="Number of Bots:", style="Setup.TLabel").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.bot_count_var = tk.IntVar(value=self.bot_count) # Variable to store selection
        bot_count_frame = ttk.Frame(options_frame, style="Setup.TFrame") # Frame to hold radio buttons
        for i in range(1, 4): # Allow 1 to 3 bots
             rb = ttk.Radiobutton(bot_count_frame, text=str(i), variable=self.bot_count_var, value=i)
             rb.pack(side=tk.LEFT, padx=5)
        bot_count_frame.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Bot Difficulty Selection
        ttk.Label(options_frame, text="Bot Difficulty:", style="Setup.TLabel").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.bot_difficulty_var = tk.StringVar(value=self.bot_difficulty) # Variable for difficulty
        difficulty_frame = ttk.Frame(options_frame, style="Setup.TFrame")
        ttk.Radiobutton(difficulty_frame, text="Easy", variable=self.bot_difficulty_var, value="easy").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(difficulty_frame, text="Hard", variable=self.bot_difficulty_var, value="hard").pack(side=tk.LEFT, padx=5) # Add "Hard" option if implemented
        difficulty_frame.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Start Game Button
        self.start_button = ttk.Button(self.setup_frame, text="Make the Deal", command=self.start_game, style="Action.TButton", width=20)
        self.start_button.grid(row=2, column=1, pady=(40, 20))


    def _create_game_widgets(self):
        """Creates the widgets for the main game screen (initially hidden)."""
        # --- Grid Configuration for Game Frame ---
        self.game_frame.columnconfigure(0, weight=1) # Left Bot Area / Exit Button Col
        self.game_frame.columnconfigure(1, weight=1) # Center Area (Community Cards, Pot) Col
        self.game_frame.columnconfigure(2, weight=1) # Right Bot Area Col
        self.game_frame.rowconfigure(0, weight=1) # Top Bot Area Row
        self.game_frame.rowconfigure(1, weight=1) # Middle Area Row (Pot/Info, maybe Bot)
        self.game_frame.rowconfigure(2, weight=3) # Player Area Row (more weight)
        self.game_frame.rowconfigure(3, weight=0, minsize=50) # Bottom Row for Return Button, give min height

        # --- Community Card Area (Center Top) ---
        community_frame = ttk.LabelFrame(self.game_frame, text="Community Cards", padding="10", style="GreenBG.TLabelframe")
        community_frame.grid(row=0, column=1, rowspan=1, pady=10, sticky="n") # Place North
        self.community_card_labels = []
        card_area_frame = ttk.Frame(community_frame, style="Game.TFrame") # Inner frame for cards
        card_area_frame.pack(expand=True, pady=5)
        for i in range(5):
            # Create label, use card back image initially or blank if missing
            img_to_use = self.card_back_image if self.card_back_image else ImageTk.PhotoImage(Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), self.TABLE_GREEN)) # Blank placeholder
            lbl = ttk.Label(card_area_frame, image=img_to_use, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = img_to_use # Keep reference
            lbl.pack(side=tk.LEFT, padx=3)
            self.community_card_labels.append(lbl)

        # --- Pot and Bet Info Area (Center Middle) ---
        info_frame = ttk.Frame(self.game_frame, padding="10", style="Game.TFrame")
        info_frame.grid(row=1, column=1, pady=5, sticky="n") # Place below community cards
        info_frame.columnconfigure(0, weight=1)
        self.pot_label = ttk.Label(info_frame, text="Pot: 0", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.pot_label.grid(row=0, column=0, pady=2, sticky="ew")
        self.current_bet_label = ttk.Label(info_frame, text="Current Bet: 0", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.current_bet_label.grid(row=1, column=0, pady=2, sticky="ew")
        self.current_turn_label = ttk.Label(info_frame, text="Turn: -", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.current_turn_label.grid(row=2, column=0, pady=2, sticky="ew")

        # --- Player Area (Bottom Row spanning columns) ---
        player_frame = ttk.LabelFrame(self.game_frame, text="You", padding="10", style="GreenBG.TLabelframe")
        player_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="nsew")
        # Configure columns inside player frame for layout
        player_frame.columnconfigure(0, weight=1) # Stats area
        player_frame.columnconfigure(1, weight=2) # Cards area (wider)
        player_frame.columnconfigure(2, weight=1) # Actions area

        # Player Stats (Left side of Player Area)
        player_stats_frame = ttk.Frame(player_frame, style="Game.TFrame")
        player_stats_frame.grid(row=0, column=0, sticky="nw", padx=10, pady=5)
        self.player_chips_label = ttk.Label(player_stats_frame, text=f"Chips: {self.STARTING_CHIPS}", style="GreenBG.TLabel")
        self.player_chips_label.pack(anchor="w", pady=2)
        self.player_hearts_label = ttk.Label(player_stats_frame, text=f"Hearts: {self.HEART_ICON * INITIAL_HEARTS}", style="Hearts.TLabel")
        self.player_hearts_label.pack(anchor="w", pady=2)

        # Player Cards (Center of Player Area)
        cards_frame = ttk.Frame(player_frame, style="Game.TFrame")
        cards_frame.grid(row=0, column=1, pady=5, sticky="n") # Center horizontally
        self.player_card_labels = []
        img_to_use = self.card_back_image if self.card_back_image else ImageTk.PhotoImage(Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), self.TABLE_GREEN))
        for i in range(2):
            lbl = ttk.Label(cards_frame, image=img_to_use, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = img_to_use
            lbl.pack(side=tk.LEFT, padx=5)
            self.player_card_labels.append(lbl)

        # Action Buttons (Right side of Player Area)
        action_frame = ttk.Frame(player_frame, style="Game.TFrame")
        action_frame.grid(row=0, column=2, padx=10, pady=5, sticky="ne")
        # Create buttons, initially disabled, use specific style
        btn_width = 10
        self.check_button = ttk.Button(action_frame, text="Check", command=lambda: self.handle_human_action("check", 0), state=tk.DISABLED, style="Action.TButton", width=btn_width)
        self.check_button.pack(pady=3, fill=tk.X)
        self.call_button = ttk.Button(action_frame, text="Call", command=lambda: self.handle_human_action("call", 0), state=tk.DISABLED, style="Action.TButton", width=btn_width)
        self.call_button.pack(pady=3, fill=tk.X)
        self.fold_button = ttk.Button(action_frame, text="Fold", command=lambda: self.handle_human_action("fold", 0), state=tk.DISABLED, style="Action.TButton", width=btn_width)
        self.fold_button.pack(pady=3, fill=tk.X)
        # Frame for Raise button and entry field
        raise_frame = ttk.Frame(action_frame, style="Game.TFrame")
        raise_frame.pack(pady=3, fill=tk.X)
        self.raise_button = ttk.Button(raise_frame, text="Raise", command=self.handle_raise_prompt, state=tk.DISABLED, style="Action.TButton")
        self.raise_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))
        self.raise_amount_var = tk.StringVar() # Variable for raise amount entry
        self.raise_entry = ttk.Entry(raise_frame, width=7, textvariable=self.raise_amount_var, state=tk.DISABLED, font=self.status_font)
        self.raise_entry.pack(side=tk.LEFT)
        self.all_in_button = ttk.Button(action_frame, text="All In", command=lambda: self.handle_human_action("all in", 0), state=tk.DISABLED, style="Action.TButton", width=btn_width)
        self.all_in_button.pack(pady=3, fill=tk.X)

        # --- Bot Area Placeholders ---
        self.bot_widgets = {}
        # Define intended grid positions for layout logic later
        self._create_bot_area_placeholder("Bot_1", 0, 0) # Top Left
        self._create_bot_area_placeholder("Bot_2", 0, 2) # Top Right
        self._create_bot_area_placeholder("Bot_3", 1, 0) # Mid Left (below Bot 1)

        # --- Return to Menu Button (Bottom Row, Left Column) ---
        self.return_button = ttk.Button(self.game_frame,
                                        text="Return to Menu",
                                        command=self._return_to_menu, # Use the dedicated method
                                        style="TButton", width=15)
        self.return_button.grid(row=3, column=0, padx=10, pady=10, sticky="sw") # Place at bottom-left


    def _create_bot_area_placeholder(self, placeholder_name, grid_row, grid_col):
        """Creates the widgets for a bot display area but doesn't grid it."""
        frame = ttk.LabelFrame(self.game_frame, text=placeholder_name, padding="5", style="GreenBG.TLabelframe")

        info_label = ttk.Label(frame, text=f"Chips: {self.STARTING_CHIPS}", anchor="w", style="GreenBG.TLabel")
        info_label.pack(pady=2, fill=tk.X)
        status_label = ttk.Label(frame, text="Status: Waiting", anchor="w", style="GreenBG.TLabel")
        status_label.pack(pady=2, fill=tk.X)

        cards_frame = ttk.Frame(frame, style="Game.TFrame")
        cards_frame.pack(pady=5)
        card_labels = []
        img_to_use = self.card_back_image if self.card_back_image else ImageTk.PhotoImage(Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), self.TABLE_GREEN))
        for i in range(2): # Bots have 2 hole cards
            lbl = ttk.Label(cards_frame, image=img_to_use, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = img_to_use # Keep reference
            lbl.pack(side=tk.LEFT, padx=3)
            card_labels.append(lbl)

        self.bot_widgets[placeholder_name] = {
            'frame': frame, 'info_label': info_label, 'status_label': status_label,
            'card_labels': card_labels,
            'intended_row': grid_row, 'intended_col': grid_col
        }


    def add_log_message(self, message):
        """Appends a message to the log text area, handling potential widget errors."""
        if self.log_text and self.log_text.winfo_exists(): # Check if widget exists
            try:
                self.log_text.config(state=tk.NORMAL) # Enable writing
                self.log_text.insert(tk.END, message + "\n") # Add message and newline
                self.log_text.see(tk.END) # Scroll to the end
                self.log_text.config(state=tk.DISABLED) # Disable writing again
            except tk.TclError as e:
                print(f"Log widget TclError (likely closing): {e}", message)
            except Exception as e:
                 print(f"Error adding log message: {e}", message)
        else:
            print(f"LOG (GUI not ready): {message}")


    def start_game(self):
        """Gets setup options, initializes the PokerGame instance, and switches view."""
        self.player_name = self.name_entry.get().strip() or "Player" # Get name, default if empty
        self.bot_count = self.bot_count_var.get()
        self.bot_difficulty = self.bot_difficulty_var.get()

        # Validate bot count (should be between 1 and 3 based on setup)
        if not (1 <= self.bot_count <= 3):
             messagebox.showerror("Setup Error", "Invalid number of bots selected.")
             return

        self.game = None # Ensure game object is reset
        try:
            print(f"DEBUG GUI: Creating PokerGame with P:{self.player_name}, B:{self.bot_count}, D:{self.bot_difficulty}, H:{INITIAL_HEARTS}, C:{self.STARTING_CHIPS}")
            self.game = PokerGame(
                player_name=self.player_name,
                bot_count=self.bot_count,
                bot_difficulty=self.bot_difficulty,
                initial_hearts=INITIAL_HEARTS,
                initial_chips=self.STARTING_CHIPS
            )
        except NameError as e:
             messagebox.showerror("Setup Error", f"A required name is not defined (check imports/constants): {e}")
             traceback.print_exc(); self.game = None; return
        except TypeError as e:
             messagebox.showerror("Setup Error", f"Mismatch in arguments for PokerGame setup: {e}\nCheck PokerGame.__init__ signature.")
             traceback.print_exc(); self.game = None; return
        except Exception as e:
            messagebox.showerror("Setup Error", f"Failed to initialize game logic: {e}")
            traceback.print_exc(); self.game = None; return

        # --- Configure Bot Displays based on actual game setup ---
        self._configure_bot_displays() # Place bot widgets correctly

        # --- Switch from Setup View to Game View ---
        self.setup_frame.pack_forget() # Hide setup widgets
        self.game_frame.pack(fill=tk.BOTH, expand=True) # Show game widgets
        # Ensure log frame is visible below game frame
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5) # Re-pack log frame

        # Log initial messages
        self.add_log_message(f"--- Game Started: {self.player_name} vs {self.bot_count} Bot(s) ({self.bot_difficulty}) ---")
        self.add_log_message(f"Starting with {self.STARTING_CHIPS} chips and {INITIAL_HEARTS} hearts.")
        self.add_log_message("The Devil deals...")

        # Start the first round of the game
        self.start_new_round()


    def _configure_bot_displays(self):
        """Grids the bot frames in their intended positions based on the number of bots."""
        # Hide all placeholders first in case of restart
        for widgets in self.bot_widgets.values():
             if widgets['frame'].winfo_exists():
                 widgets['frame'].grid_forget()

        if not self.game:
            print("ERROR: _configure_bot_displays called but self.game is None.")
            return

        # Get actual bot names from the game instance's players dictionary
        bot_names_in_game = [name for name, p_data in self.game.players.items() if p_data.get('is_bot')]

        if not bot_names_in_game:
             print("DEBUG GUI: No bot names found in game instance for display configuration.")
             return

        # Map actual bot names to placeholder widgets based on intended positions
        placeholder_keys = list(self.bot_widgets.keys()) # ["Bot_1", "Bot_2", "Bot_3"]

        # Grid the frames for the actual number of bots created
        for i, actual_bot_name in enumerate(bot_names_in_game):
            if i < len(placeholder_keys):
                 placeholder_key = placeholder_keys[i]
                 widgets_to_place = self.bot_widgets[placeholder_key]
                 grid_row = widgets_to_place['intended_row']
                 grid_col = widgets_to_place['intended_col']

                 widgets_to_place['frame'].config(text=actual_bot_name) # Set the LabelFrame title
                 widgets_to_place['frame'].grid(row=grid_row, column=grid_col, padx=5, pady=5, sticky="nsew")
                 print(f"DEBUG GUI: Placed bot '{actual_bot_name}' at grid ({grid_row},{grid_col}) using placeholder {placeholder_key}")
            else:
                 print(f"Warning: More bots ({len(bot_names_in_game)}) than defined placeholders ({len(placeholder_keys)}). Bot '{actual_bot_name}' not displayed.")
                 break


    def start_new_round(self):
        """Initiates a new round in the game logic and updates the UI."""
        if not self.game:
            print("ERROR: start_new_round called but game logic is not initialized.")
            return

        # Check game over status *before* trying to start (catches bust/heart loss from previous round)
        is_over, _, reason = self.game.check_game_over_status()
        if is_over:
            print(f"DEBUG GUI: start_new_round found game is already over (Reason: {reason}).")
            # Need to ensure the game over sequence runs if not already handled
            if not self.game.game_over_handled:
                 self.check_game_over() # Trigger game over sequence
            return

        self.add_log_message("\n" + "="*15 + " Starting New Round " + "="*15)
        try:
            # Tell the backend to reset for a new round and get initial info
            round_info = self.game.start_new_round_get_info()

            # Validate the received information
            if not round_info:
                 raise ValueError("Backend returned no information for new round.")
            if 'error' in round_info:
                err_msg = round_info.get('error', 'Unknown error starting round.')
                # If backend reports game over during start, ensure GUI reflects it
                if round_info.get('game_over'):
                    self.game.game_over = True
                    if not self.game.game_over_handled: self.check_game_over() # Trigger handler
                else:
                    # Assume fatal error if round start fails critically without game over flag
                    messagebox.showerror("Round Error", err_msg)
                    if self.game: self.game.game_over = True
                    if not self.game.game_over_handled: self.check_game_over()
                return

            # Extract info for logging
            dealer_name = round_info.get('dealer', '?')
            sb_player = round_info.get('sb_player', '?')
            sb_amount = round_info.get('sb_amount', '?')
            bb_player = round_info.get('bb_player', '?')
            bb_amount = round_info.get('bb_amount', '?')
            self.turn_order = round_info.get('turn_order', []) # Use backend's turn order
            self.current_player_index = round_info.get('start_index', -1) # Use backend's start index


            # Log the blinds posting messages
            self.add_log_message(f"Dealer button is on {dealer_name}.")
            self.add_log_message(f"{sb_player} posts small blind {sb_amount}.")
            self.add_log_message(f"{bb_player} posts big blind {bb_amount}.")

            # Check if turn order is valid, essential for gameplay flow
            if not self.turn_order or self.current_player_index < 0:
                 print("Warning GUI: StartNewRound returned invalid turn order or start index.")
                 # Betting might be over immediately if everyone is all-in
                 self.update_ui() # Update UI with dealt cards etc.
                 self.root.after(100, self.process_next_turn) # Check turn processing anyway
                 return

            # Update UI for the new round start
            self.update_ui()
            self.root.update() # Ensure UI draws immediately

            # Trigger the first turn processing after a short delay
            self.root.after(300, self.process_next_turn) # Slightly longer delay maybe

        except AttributeError as e:
            messagebox.showerror("Round Error", f"Game logic error (missing method/attribute): {e}")
            traceback.print_exc()
            if self.game: self.game.game_over = True
            if not self.game.game_over_handled: self.check_game_over()
        except ValueError as e:
            messagebox.showerror("Round Error", f"Data error starting round: {e}")
            traceback.print_exc()
            if self.game: self.game.game_over = True
            if not self.game.game_over_handled: self.check_game_over()
        except Exception as e:
            messagebox.showerror("Round Error", f"Unexpected error starting round: {e}")
            traceback.print_exc()
            if self.game: self.game.game_over = True
            if not self.game.game_over_handled: self.check_game_over()


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
                 self.disable_all_buttons()
                 self.pot_label.config(text="Pot: Error"); self.current_bet_label.config(text="Bet: Error")
                 self.current_turn_label.config(text="Turn: Error")
                 return

            # --- Update Center Info Area ---
            self.pot_label.config(text=f"Pot: {state.get('pot', 'N/A')}")
            self.current_bet_label.config(text=f"Current Bet: {state.get('current_bet', 'N/A')}")
            # Get current player directly from backend state for turn label accuracy
            current_player_name = state.get('current_turn_player', "-")
            self.current_turn_label.config(text=f"Turn: {current_player_name}")
            current_stage_name = state.get('current_stage', 'Unknown')
            # Optional: Display stage name somewhere if needed
            # self.stage_label.config(text=f"Stage: {current_stage_name.capitalize()}")

            # --- Update Community Cards ---
            community_cards_data = state.get('community_cards', [])
            img_blank = ImageTk.PhotoImage(Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), self.TABLE_GREEN)) # Blank card image
            for i, lbl in enumerate(self.community_card_labels):
                img = self.card_back_image # Default to back
                card_code = None
                if i < len(community_cards_data):
                    card_code = community_cards_data[i] # Get card code like 'As' or 'Td'

                if card_code: # If there is a card for this position
                     img = self.card_images.get(card_code) # Get loaded image
                # Use back image if card_code was None, use loaded image if found, else use blank
                final_img = self.card_back_image if card_code is None else (img if img else img_blank)
                # Ensure final_img is not None before configuring
                if final_img is None: final_img = img_blank
                lbl.config(image=final_img)
                lbl.image = final_img # Keep reference

            # --- Update Player Area ---
            player_state_data = state['players'].get(self.player_name)
            if player_state_data:
                status_text = ""
                if player_state_data.get('folded'): status_text = " (Folded)"
                if player_state_data.get('all_in'): status_text = " (ALL IN)"
                self.player_chips_label.config(text=f"Chips: {player_state_data.get('chips', 0)}{status_text}")
                hearts = player_state_data.get('hearts', 0)
                self.player_hearts_label.config(text=f"Hearts: {self.HEART_ICON * hearts}")
                # Update player hole cards
                player_cards_data = player_state_data.get('cards', [])
                for i, lbl in enumerate(self.player_card_labels):
                    img = img_blank # Default to blank
                    if i < len(player_cards_data) and player_cards_data[i]:
                        loaded_img = self.card_images.get(player_cards_data[i])
                        if loaded_img: img = loaded_img
                    # Ensure img is valid
                    if img is None: img = img_blank
                    lbl.config(image=img)
                    lbl.image = img
            else:
                 self.player_chips_label.config(text="Chips: -"); self.player_hearts_label.config(text="Hearts: -")

            # --- Update Bot Areas ---
            bot_names_in_game = [name for name, p_data in state['players'].items() if p_data.get('is_bot')]
            placeholder_keys = list(self.bot_widgets.keys())

            for i, actual_bot_name in enumerate(bot_names_in_game):
                 if i < len(placeholder_keys):
                      placeholder_key = placeholder_keys[i]
                      widgets = self.bot_widgets.get(placeholder_key)
                      if not widgets or not widgets['frame'].winfo_exists(): continue

                      bot_state_data = state['players'].get(actual_bot_name)
                      if bot_state_data:
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
                                    (show_bot_cards or current_stage_name == "showdown"):
                                     loaded_img = self.card_images.get(bot_cards_data[j])
                                     if loaded_img: img = loaded_img # Use loaded image if found
                                 # Use blank if back/face image missing
                                 final_img = img if img else img_blank
                                 # Ensure final_img is not None
                                 if final_img is None: final_img = img_blank
                                 lbl.config(image=final_img)
                                 lbl.image = final_img
                      else:
                            widgets['info_label'].config(text="Chips: -"); widgets['status_label'].config(text="Status: Unknown")

            # --- Enable/Disable Action Buttons ---
            # Check if it's the human player's turn AND game/round not over
            if current_player_name == self.player_name and \
               not getattr(self.game, 'round_over', False) and \
               not getattr(self.game, 'game_over', False):
                # Check player status again from latest state
                player_state_now = state['players'].get(self.player_name)
                if player_state_now and not player_state_now.get('folded') and not player_state_now.get('all_in'):
                     print(f"DEBUG GUI UpdateUI: Enabling buttons for {self.player_name}")
                     self.update_action_buttons() # Logic to enable/disable specific buttons
                else:
                     print(f"DEBUG GUI UpdateUI: Disabling buttons for {self.player_name} (State: Folded/AllIn)")
                     self.disable_all_buttons()
            else:
                # Not player's turn, or round/game over
                # print(f"DEBUG GUI UpdateUI: Disabling buttons (Turn: {current_player_name}, RoundOver: {getattr(self.game, 'round_over', False)}, GameOver: {getattr(self.game, 'game_over', False)})")
                self.disable_all_buttons()

        except tk.TclError as e:
            print(f"TclError during UI update (likely closing window): {e}")
        except AttributeError as e:
            print(f"AttributeError during UI update (check game state or widget names): {e}")
            traceback.print_exc()
        except Exception as e:
            messagebox.showerror("UI Update Error", f"Unexpected error during UI update: {e}")
            traceback.print_exc()


    def update_action_buttons(self):
        """Enables/disables specific action buttons based on current game state and player chips."""
        if not self.game: return

        try:
            state = self.game.get_game_state_summary()
            player_state = state['players'].get(self.player_name)

            if not player_state or player_state.get('folded') or player_state.get('all_in'):
                 self.disable_all_buttons()
                 return

            chips = player_state.get('chips', 0)
            current_bet = state.get('current_bet', 0)
            player_bet_this_round = player_state.get('current_round_bet', 0)
            amount_to_call = max(0, current_bet - player_bet_this_round)
            big_blind = state.get('big_blind', 20) # Get BB from state
            previous_bet = state.get('previous_bet', 0) # Get prev bet from state

            # --- Enable/Disable Fold Button ---
            self.fold_button.config(state=tk.NORMAL)

            # --- Enable/Disable Check / Call Buttons ---
            can_check = (amount_to_call <= 0)
            self.check_button.config(state=tk.NORMAL if can_check else tk.DISABLED)

            if not can_check: # Must call, raise, or fold
                 actual_call_cost = min(amount_to_call, chips)
                 if chips >= amount_to_call: # Can afford the full call
                     self.call_button.config(state=tk.NORMAL, text=f"Call {amount_to_call}")
                 elif chips > 0: # Cannot afford full call, but can call with remaining chips (all-in)
                     self.call_button.config(state=tk.NORMAL, text=f"Call {chips} (All In)")
                 else: # No chips left, cannot call
                     self.call_button.config(state=tk.DISABLED, text="Call")
            else: # Check is available
                self.call_button.config(state=tk.DISABLED, text="Call")

            # --- Enable/Disable Raise / All-in Buttons ---
            can_potentially_raise = chips > amount_to_call

            if can_potentially_raise:
                min_raise_increment = max(big_blind, current_bet - previous_bet if current_bet > previous_bet else big_blind)
                min_legal_total_bet_target = current_bet + min_raise_increment
                # Min additional chips needed beyond call
                min_additional_chips_for_raise = max(1, min_legal_total_bet_target - player_bet_this_round) if min_legal_total_bet_target > player_bet_this_round else 0
                # Can player afford the min raise cost (call + additional)?
                can_afford_minimum_raise = chips >= (amount_to_call + min_additional_chips_for_raise) if min_additional_chips_for_raise > 0 else False

                if can_afford_minimum_raise:
                     # Max player can raise to (all-in)
                     max_raise_total_bet = player_bet_this_round + chips
                     self.raise_button.config(state=tk.NORMAL, text=f"Raise") # Simpler text
                     self.raise_entry.config(state=tk.NORMAL)
                     # Optionally pre-fill entry with min raise total
                     # self.raise_amount_var.set(str(min_legal_total_bet_target))
                else:
                     self.raise_button.config(state=tk.DISABLED, text="Raise")
                     self.raise_entry.config(state=tk.DISABLED); self.raise_amount_var.set("")
            else:
                self.raise_button.config(state=tk.DISABLED, text="Raise")
                self.raise_entry.config(state=tk.DISABLED); self.raise_amount_var.set("")

            # --- Enable/Disable All-in Button ---
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
        # Add checks for widget existence before configuring
        if hasattr(self, 'check_button') and self.check_button.winfo_exists(): self.check_button.config(state=tk.DISABLED)
        if hasattr(self, 'call_button') and self.call_button.winfo_exists(): self.call_button.config(state=tk.DISABLED, text="Call")
        if hasattr(self, 'fold_button') and self.fold_button.winfo_exists(): self.fold_button.config(state=tk.DISABLED)
        if hasattr(self, 'raise_button') and self.raise_button.winfo_exists(): self.raise_button.config(state=tk.DISABLED, text="Raise")
        if hasattr(self, 'raise_entry') and self.raise_entry.winfo_exists(): self.raise_entry.config(state=tk.DISABLED); self.raise_amount_var.set("")
        if hasattr(self, 'all_in_button') and self.all_in_button.winfo_exists(): self.all_in_button.config(state=tk.DISABLED, text="All In")


    def handle_human_action(self, action, total_bet_amount=0):
        """Processes the human player's chosen action by calling the backend."""
        if not self.game or self.game.game_over or self.game.round_over:
            print(f"DEBUG GUI: Action '{action}' ignored, game/round over.")
            return
        if self.human_action_taken:
            print(f"DEBUG GUI: Action '{action}' ignored, action already taken this turn.")
            return

        # Verify with backend that it *is* the player's turn
        try:
            current_state = self.game.get_game_state_summary()
            backend_turn = current_state.get('current_turn_player')
            if backend_turn != self.player_name:
                 print(f"ERROR GUI: handle_human_action called for {self.player_name} but backend turn is {backend_turn}. Ignoring.")
                 return
        except Exception as e:
            print(f"ERROR GUI: Failed verify turn in handle_human_action: {e}"); return

        # Mark action as taken and disable buttons immediately
        self.human_action_taken = True
        self.disable_all_buttons()
        self.root.update_idletasks() # Make button disabling visible quickly

        player_state = current_state['players'].get(self.player_name)
        if not player_state:
            print(f"ERROR GUI: Player state for {self.player_name} not found."); self.human_action_taken = False; return

        chips = player_state.get('chips', 0)
        player_bet_this_round = player_state.get('current_round_bet', 0)
        current_bet = current_state.get('current_bet', 0)

        # Determine final bet amount and log message
        final_total_round_bet = player_bet_this_round # Default
        action_log = action.capitalize()
        processed_action = action # Action name sent to backend

        try:
            if action == "call":
                amount_to_call = max(0, current_bet - player_bet_this_round)
                call_chip_cost = min(amount_to_call, chips)
                final_total_round_bet = player_bet_this_round + call_chip_cost
                is_all_in_call = (call_chip_cost > 0 and call_chip_cost >= chips) # >= catches edge case of exactly 0 chips left
                action_log = f"Call {call_chip_cost}" + (" (All In)" if is_all_in_call else "")
                if is_all_in_call and call_chip_cost > 0: processed_action = "all in" # Send 'all in' if call uses all chips

            elif action == "all in":
                final_total_round_bet = player_bet_this_round + chips
                action_log = f"All In ({chips})"
                processed_action = "all in"

            elif action == "raise":
                final_total_round_bet = total_bet_amount # Already validated by handle_raise_prompt
                raise_increment = final_total_round_bet - player_bet_this_round
                is_all_in_raise = (raise_increment >= chips) # If raise cost is all chips (or more, capped)
                action_log = f"Raise to {final_total_round_bet} (+{raise_increment})" + (" (All In)" if is_all_in_raise else "")
                if is_all_in_raise:
                    processed_action = "all in"
                    final_total_round_bet = player_bet_this_round + chips # Ensure bet amount matches all chips if all-in raise

            # Log and Send to Backend
            self.add_log_message(f"{self.player_name}: {action_log}")
            # Pass the potentially modified action name and the final total bet for the round
            self.game.process_player_action(self.player_name, processed_action, final_total_round_bet)

            # Update UI immediately after processing (shows chip/pot changes)
            self.update_ui()
            self.root.update()

            # Schedule the check for the *next* turn
            self.root.after(150, self.process_next_turn)

        except ValueError as e: # Catch validation errors from backend (e.g., illegal raise)
            messagebox.showerror("Action Error", str(e))
            self.human_action_taken = False # Allow action again
            self.update_ui() # Re-enable buttons if still player's turn
        except Exception as e:
            messagebox.showerror("Game Error", f"Error processing action: {e}")
            traceback.print_exc()
            if self.game: self.game.game_over = True # Assume fatal error
            self.human_action_taken = False # Reset flag
            if not self.game.game_over_handled: self.check_game_over() # Trigger game over


    def handle_raise_prompt(self):
        """Handles the raise action: validates input from entry or prompts player."""
        if not self.game: return

        try:
            state = self.game.get_game_state_summary()
            player_state = state['players'].get(self.player_name)
            if not player_state or player_state.get('folded') or player_state.get('all_in'): return

            chips = player_state.get('chips', 0)
            current_bet = state.get('current_bet', 0)
            player_bet_this_round = player_state.get('current_round_bet', 0)
            previous_bet = state.get('previous_bet', 0)
            big_blind = state.get('big_blind', 20)
            amount_to_call = max(0, current_bet - player_bet_this_round)

            # Calculate Minimum Legal Raise
            min_raise_increment = max(big_blind, current_bet - previous_bet if current_bet > previous_bet else big_blind)
            min_legal_total_bet_target = current_bet + min_raise_increment
            max_possible_total_bet = player_bet_this_round + chips # All-in amount
            # Actual minimum player CAN raise to (capped by their stack)
            min_player_can_raise_to = min(min_legal_total_bet_target, max_possible_total_bet)
            # Min additional chips needed for the minimum valid raise
            min_additional_chips_needed = max(0, min_player_can_raise_to - player_bet_this_round)


            # Check if ANY raise is possible
            can_afford_min_raise = chips >= (amount_to_call + min_additional_chips_needed) if min_additional_chips_needed > 0 else chips > amount_to_call

            if not can_afford_min_raise:
                 messagebox.showinfo("Raise Info", "Not enough chips to make a valid raise over the current bet.")
                 return

            # Get Raise Amount (from entry or dialog)
            target_total_bet_str = self.raise_amount_var.get().strip()
            target_total_bet = 0

            try:
                if target_total_bet_str:
                     target_total_bet = int(target_total_bet_str)
                     # Validate amount entered in the box
                     if target_total_bet < min_player_can_raise_to:
                          messagebox.showwarning("Invalid Raise Amount", f"Minimum total bet required is {min_player_can_raise_to}.")
                          self.raise_amount_var.set(str(min_player_can_raise_to)) # Suggest minimum
                          return
                     if target_total_bet > max_possible_total_bet:
                          messagebox.showwarning("Invalid Raise Amount", f"Cannot bet more than your stack ({max_possible_total_bet}).")
                          self.raise_amount_var.set(str(max_possible_total_bet)) # Suggest all-in
                          return
                else:
                    # Prompt using simpledialog if entry is empty
                    prompt_val = simpledialog.askinteger("Raise To",
                                                     f"Enter the TOTAL amount you want to bet this round.\n\n"
                                                     f"(Current high bet: {current_bet}, You have bet: {player_bet_this_round})\n"
                                                     f"Minimum Total Bet: {min_player_can_raise_to}\n"
                                                     f"Maximum Bet (All In): {max_possible_total_bet}",
                                                     parent=self.root,
                                                     initialvalue=min_player_can_raise_to,
                                                     minvalue=min_player_can_raise_to,
                                                     maxvalue=max_possible_total_bet)
                    if prompt_val is None: return # User cancelled
                    target_total_bet = prompt_val

                # Process the Validated Raise Action
                self.handle_human_action("raise", target_total_bet)

            except ValueError:
                messagebox.showwarning("Invalid Input","Please enter a valid whole number for the total bet amount.")
                self.raise_amount_var.set(str(min_player_can_raise_to)) # Reset entry
            except Exception as e: messagebox.showerror("Error", f"Error during raise input: {e}"); traceback.print_exc()

        except Exception as e: messagebox.showerror("Raise Error", f"Error preparing raise prompt: {e}"); traceback.print_exc()


    def process_next_turn(self):
        """Checks game state and decides whether to wait for human, trigger bot, or advance stage."""
        print(f"DEBUG GUI: process_next_turn triggered.")
        if not self.game: print("ERROR GUI: process_next_turn - game is None."); return
        if self.game.game_over: print("DEBUG GUI: process_next_turn - game is over."); self.check_game_over(); return # Ensure handled
        if self.game.round_over: print("DEBUG GUI: process_next_turn - round is over."); self.root.after(50, self.determine_winner_and_proceed); return

        try:
            state = self.game.get_game_state_summary()
            is_betting_over = self.game.is_betting_over() # Ask backend if betting round finished
            current_player_name = state.get('current_turn_player') # Who backend thinks should act
            current_stage = state.get('current_stage', 'N/A')

            print(f"DEBUG GUI process_next_turn: Stage={current_stage}, Turn={current_player_name}, BettingOver={is_betting_over}")

        except Exception as e:
             messagebox.showerror("Game State Error", f"Failed to get/process game state: {e}")
             traceback.print_exc();
             if self.game: self.game.game_over = True
             if not self.game.game_over_handled: self.check_game_over(); return

        # --- Decide Next Step ---
        if is_betting_over:
            print(f"DEBUG GUI: Betting is over for {current_stage}. Advancing stage.")
            self.update_ui() # Show final bets for this stage
            self.root.after(200, self.advance_game_stage) # Schedule stage advancement

        elif current_player_name is None:
             # Should not happen if betting isn't over, indicates state issue
             print("ERROR GUI: Backend reported betting not over, but no current player! Advancing stage as fallback.")
             self.add_log_message("Warning: Turn inconsistency detected. Advancing stage.")
             self.root.after(100, self.advance_game_stage)

        elif current_player_name == self.player_name:
             print(f"DEBUG GUI: Waiting for human player ({self.player_name}) action.")
             self.human_action_taken = False # Reset flag, allow player to click
             self.update_ui() # Update UI (should enable buttons)

        else: # It's a bot's turn
             print(f"DEBUG GUI: Triggering action for bot: {current_player_name}")
             self.update_ui() # Update UI to show it's bot's turn
             self.root.update() # Force redraw before bot "thinks"
             think_time = random.randint(400, 1200) # Shorter delay maybe
             self.root.after(think_time, self.get_bot_action, current_player_name)


    def get_bot_action(self, bot_name):
        """Gets and processes the specified bot's action from the game logic."""
        if not self.game or self.game.round_over or self.game.game_over:
            print(f"DEBUG GUI: get_bot_action for {bot_name} skipped, round/game over.")
            return

        # Verify backend agrees it's this bot's turn (optional safety)
        try:
            backend_turn = self.game.get_game_state_summary().get('current_turn_player')
            if backend_turn != bot_name:
                print(f"ERROR GUI: get_bot_action called for {bot_name} but backend turn is {backend_turn}. Re-checking turn.")
                self.root.after(50, self.process_next_turn); return
        except Exception as e: print(f"ERROR GUI: Failed verify turn in get_bot_action: {e}")

        # --- Get and Process Bot Action ---
        try:
            # Call backend method to get bot's decision
            action, total_bet_amount = self.game.get_bot_action_gui(bot_name)

            # Get bot's state for logging calculations
            player_state = self.game.players.get(bot_name)
            chips = player_state.get('chips', 0) if player_state else 0
            player_bet_this_round = player_state.get('current_round_bet', 0) if player_state else 0

            # --- Determine Log Message and Final Processed Action ---
            action_log = action.capitalize()
            processed_action = action # Action sent to backend
            final_total_round_bet = 0 # For process_player_action raise arg

            if action == "call":
                current_bet = self.game.current_bet
                amount_to_call = max(0, current_bet - player_bet_this_round)
                call_chip_cost = min(amount_to_call, chips) if amount_to_call > 0 else 0
                is_all_in = (call_chip_cost > 0 and call_chip_cost >= chips)
                action_log = f"Call {call_chip_cost}" + (" (All In)" if is_all_in else "")
                if is_all_in and call_chip_cost > 0: processed_action = "all in"
                final_total_round_bet = player_bet_this_round + call_chip_cost # Need this for side pot logic if call cost is 0
            elif action == "raise":
                final_total_round_bet = total_bet_amount # Use amount from bot
                raise_increment = final_total_round_bet - player_bet_this_round
                is_all_in = (raise_increment >= chips)
                action_log = f"Raise to {final_total_round_bet} (+{raise_increment})" + (" (All In)" if is_all_in else "")
                if is_all_in:
                    processed_action = "all in"
                    final_total_round_bet = player_bet_this_round + chips # Cap at available chips
            elif action == "all in":
                 action_log = f"All In ({chips})"
                 processed_action = "all in"
                 final_total_round_bet = player_bet_this_round + chips
            elif action == "check": action_log = "Check"; final_total_round_bet = player_bet_this_round
            elif action == "fold": action_log = "Fold"; final_total_round_bet = player_bet_this_round

            # Log, Process Action, Update UI, Trigger Next
            self.add_log_message(f"{bot_name}: {action_log}")
            # Send the potentially modified action and the final total bet for the round
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
                 if self.game: self.game.process_player_action(bot_name, "fold", 0)
                 self.update_ui()
                 self.root.after(150, self.process_next_turn) # Trigger next turn check
             except Exception as fold_e:
                 print(f"ERROR GUI: Failed to fold bot {bot_name} after error: {fold_e}")
                 if self.game: self.game.game_over = True
                 if not self.game.game_over_handled: self.check_game_over()


    def advance_game_stage(self):
         """Tells the game logic to advance (deal flop/turn/river/showdown) and updates UI."""
         print(f"DEBUG GUI: advance_game_stage called. Current stage was: {getattr(self.game, 'current_stage', 'N/A')}")
         if not self.game: return
         if self.game.game_over: self.check_game_over(); return

         # Check for premature round end again (safety)
         try:
             if self.game.round_over:
                 print("DEBUG GUI: advance_game_stage -> Round already marked over. Determining winner.")
                 self.root.after(50, self.determine_winner_and_proceed)
                 return
             # Check based on active players again just before advancing
             state = self.game.get_game_state_summary()
             contesting = [p for n, p in state['players'].items() if not p.get('folded')]
             can_bet = [p for n, p in contesting if not p.get('all_in')]
             if len(contesting) <= 1:
                  print("DEBUG GUI: advance_game_stage -> Only <=1 contesting. Ending round.")
                  self.game.round_over = True
                  self.update_ui(show_bot_cards=True)
                  self.root.after(50, self.determine_winner_and_proceed)
                  return
             if len(can_bet) <= 1 and len(contesting) > 1:
                  print("DEBUG GUI: advance_game_stage -> Only <=1 can bet (others all-in/folded). Advancing/Showdown.")
                  # Fall through to advance stage (might lead to immediate showdown)

         except Exception as e: print(f"Error checking premature round end: {e}")

         # Ask Backend to Advance Stage
         next_stage = None
         try:
             next_stage = self.game.advance_to_next_stage() # Deals cards, updates backend stage
             print(f"DEBUG GUI: game.advance_to_next_stage() returned stage: {next_stage}. Backend stage now: {self.game.current_stage}")
         except AttributeError: messagebox.showerror("Game Error", "Game logic missing 'advance_to_next_stage'."); self.check_game_over(); return
         except Exception as e: messagebox.showerror("Stage Error", f"Error advancing game stage logic: {e}"); traceback.print_exc(); self.check_game_over(); return

         # --- Process the Result ---
         if next_stage == "showdown":
             self.add_log_message("\n--- Dealing Showdown ---")
             self.update_ui(show_bot_cards=True) # Reveal all cards
             self.root.update()
             self.root.after(700, self.determine_winner_and_proceed) # Longer delay before winner reveal

         elif next_stage in ['flop', 'turn', 'river']:
             self.add_log_message(f"\n--- Dealing {next_stage.capitalize()} ---")
             # --- Start the Betting Round for the New Stage ---
             try:
                # Reset betting state and determine who starts
                round_info = self.game.start_next_betting_round()
                new_turn_order = round_info.get('turn_order', [])
                new_start_index = round_info.get('start_index', -1)
                print(f"DEBUG GUI: New betting round ({next_stage}). Turn order: {new_turn_order}, Start index: {new_start_index}")

                # If betting skipped (e.g., everyone all-in)
                if not new_turn_order or new_start_index < 0:
                     self.add_log_message(f"(Betting skipped for {next_stage})")
                     self.update_ui() # Show new community cards
                     self.root.after(500, self.advance_game_stage) # Advance again quickly
                     return # Skip process_next_turn
             except AttributeError: messagebox.showerror("Game Error", "Game logic missing 'start_next_betting_round'."); self.check_game_over(); return
             except Exception as e: messagebox.showerror("Betting Round Error", f"Error starting betting for {next_stage}: {e}"); traceback.print_exc(); self.check_game_over(); return

             # --- Betting Round Starts ---
             self.update_ui() # Show new community cards
             self.root.update()
             print(f"DEBUG GUI: Triggering process_next_turn for new stage: {next_stage}")
             self.root.after(500, self.process_next_turn) # Delay before first action prompt

         else:
              # Stage advancement failed or returned None (might mean round ended unexpectedly)
              print(f"Warning GUI: advance_to_next_stage returned {next_stage}. Checking round/game state.")
              if self.game and not self.game.round_over:
                   print("Warning: Stage advance failed but round not marked over. Determining winner.")
                   self.game.round_over = True # Mark round over
                   self.root.after(100, self.determine_winner_and_proceed)
              elif self.game and self.game.round_over:
                   # Round already ended, maybe player folded last? Check game over.
                   print("Warning: Stage advance failed, round was already over. Checking game over.")
                   self.check_game_over()
              else: print("ERROR GUI: Game object missing after failed stage advance.")


    def determine_winner_and_proceed(self):
        """Calls backend to determine winner, displays info, and checks game over."""
        print("DEBUG GUI: determine_winner_and_proceed called.")
        if not self.game: return

        try:
            # This call now potentially triggers heart deduction in the backend
            winner_info = self.game.determine_winner_gui()
            # This display function will now check the exchange flag from backend
            self.display_winner(winner_info)
        except AttributeError as e:
            messagebox.showerror("Game Error", f"Game logic missing 'determine_winner_gui': {e}."); traceback.print_exc()
            if self.game: self.game.game_over = True
        except Exception as e:
            self.add_log_message(f"Error determining winner: {e}"); traceback.print_exc()

        # ALWAYS check game over status after determining winner
        self.root.after(1500, self.check_game_over) # Delay before checking game end


    def display_winner(self, winner_info):
        """Displays detailed winner information and hand results in the log area."""
        if not winner_info: self.add_log_message("\nError: Winner information missing."); return

        winners = winner_info.get('winners', [])
        pot_displayed = winner_info.get('pot', '?') # Pot value *before* distribution for display
        distributed_pot = winner_info.get('distributed_pot', 0) # Actual amount paid out
        details = winner_info.get('details', {}) # Hand evaluation details

        # --- Log Hand Results ---
        if details:
            self.add_log_message("--- Hand Results ---")
            # Get latest state AFTER pot distribution
            try:
                current_state = self.game.get_game_state_summary()
                player_states = current_state.get('players', {})
                player_order = list(self.game.players.keys()) if hasattr(self.game, 'players') else list(details.keys())
                displayed_players = set()

                for name in player_order:
                     if name in details:
                         detail = details.get(name)
                         player_state = player_states.get(name) # Get updated state
                         if detail and player_state:
                              hole_cards = detail.get('hole_cards', player_state.get('cards', []))
                              hole_cards_str = " ".join(hole_cards) if hole_cards else "?? ??"
                              hand_type = detail.get('type', 'N/A')
                              best_5_cards = detail.get('hand', [])
                              best_5_str = " ".join(best_5_cards) if best_5_cards else ""
                              log_line = f"  {name}: "
                              if player_state.get('folded'): log_line += f"Folded ({hole_cards_str})"
                              elif hand_type == 'Default (Others Folded)': log_line += f"Wins by default ({hole_cards_str})"
                              elif hand_type in ['Mucked/Invalid', 'Eval Error', 'Eval Exception', 'N/A', 'Missing Cards', 'Eval Error (None)']: log_line += f"{hand_type} ({hole_cards_str})"
                              else: log_line += f"{hand_type} ({hole_cards_str}" + (f" -> {best_5_str})" if best_5_str else ")")
                              self.add_log_message(log_line)
                              displayed_players.add(name)

                # Display any missed players (safety)
                for name, detail in details.items():
                     if name not in displayed_players:
                         status = detail.get('type', 'Unknown')
                         hole_str = " ".join(detail.get('hole_cards',[]))
                         self.add_log_message(f"  (Other) {name}: ({hole_str}) - {status}")
            except Exception as e: print(f"Error logging hand details: {e}")

        # --- Log Winner Message ---
        if len(winners) == 1:
             self.add_log_message(f"\n---> {winners[0]} wins the pot of {distributed_pot}!")
        elif len(winners) > 1:
             win_amount = winner_info.get('win_amount', 0)
             win_msg = f"\n---> Split pot ({distributed_pot}) between: {', '.join(winners)}"
             if win_amount > 0: win_msg += f" ({win_amount} each)"
             self.add_log_message(win_msg)
        else: # No winners
             if distributed_pot > 0: self.add_log_message(f"\n--- No winner declared for pot ({pot_displayed}). Pot returned? ---")
             else: self.add_log_message("\n--- Round concludes (No contest / Pot = 0). ---")

        # --- Log Heart Changes ---
        try:
            final_human_state = self.game.get_game_state_summary()['players'].get(self.player_name)
            if final_human_state:
                 start_hearts = final_human_state.get('start_round_hearts')
                 current_hearts = final_human_state.get('hearts')

                 # Check the flag set by check_game_over_status if exchange happened
                 if getattr(self.game, '_human_exchanged_heart_flag', False):
                     self.add_log_message(f"*** {self.player_name} exchanged a heart for {HEART_CHIP_EXCHANGE_AMOUNT} chips! ({current_hearts} left) ***")
                     # Flag should be reset by backend at start of next round or check_game_over
                     if self.game: self.game._human_exchanged_heart_flag = False # Reset immediately after logging
                 # Check for loss ONLY if flag wasn't set
                 elif start_hearts is not None and current_hearts < start_hearts:
                      heart_loss = start_hearts - current_hearts
                      plural = "s" if heart_loss > 1 else ""
                      self.add_log_message(f"---> {self.player_name} lost {heart_loss} heart{plural}! ({current_hearts} left) <---")
        except Exception as e: print(f"Error logging heart changes: {e}")

        # Update UI one last time for the round
        self.update_ui(show_bot_cards=True) # Show all cards at end
        self.root.update()


    def prepare_for_next_round_or_end(self):
        """Adds 'Start Next Round' button if game is not over."""
        print("DEBUG GUI: prepare_for_next_round_or_end called.")
        if not self.game: print("DEBUG GUI: prepare... -> game object is None."); return
        if self.game.game_over: print("DEBUG GUI: prepare... -> game is over."); return

        # Clean up previous button if it exists
        if hasattr(self, 'next_round_button') and self.next_round_button and self.next_round_button.winfo_exists():
            self.next_round_button.destroy()
            delattr(self, 'next_round_button')

        # Add the button below the pot info area
        self.next_round_button = ttk.Button(self.game_frame, text="Start Next Round", command=self.click_next_round, style="Action.TButton")
        # Place below pot/bet info, centered in column 1
        self.next_round_button.grid(row=1, column=1, pady=(20, 5), sticky="s")
        print("DEBUG GUI: prepare... -> Added 'Start Next Round' button.")


    def click_next_round(self):
        """Handles the 'Start Next Round' button click."""
        print("DEBUG GUI: click_next_round called.")

        # Remove the button
        if hasattr(self, 'next_round_button') and self.next_round_button and self.next_round_button.winfo_exists():
            self.next_round_button.destroy()
            delattr(self, 'next_round_button')

        # Start the next round if game logic exists and isn't over
        if self.game and not self.game.game_over:
            # Reset round-specific UI elements (cards back to hidden)
            img_back = self.card_back_image if self.card_back_image else ImageTk.PhotoImage(Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), self.TABLE_GREEN))
            for lbl in self.community_card_labels: lbl.config(image=img_back); lbl.image = img_back
            # Reset bot cards display (already done by update_ui without show_bot_cards=True)
            self.start_new_round()
        elif self.game and self.game.game_over: messagebox.showinfo("Game Over", "The game has already ended.")
        else: messagebox.showerror("Error", "Game logic is missing or not initialized.")


    def check_game_over(self):
        """Checks game over status with backend and triggers appropriate UI action."""
        print("DEBUG GUI: check_game_over called.")
        if not self.game: return
        if self.game.game_over_handled: print("DEBUG GUI: check_game_over - already handled."); return # Already processed

        # Ensure UI shows final state of the round
        try: self.update_ui(show_bot_cards=True); self.root.update_idletasks()
        except tk.TclError: pass # Ignore UI error if closing

        is_over, message, reason = False, "Game ended unexpectedly.", "unknown"
        try:
            is_over, message, reason = self.game.check_game_over_status() # This sets game_over_handled in backend if true
            print(f"DEBUG GUI: check_game_over_status() -> is_over={is_over}, reason='{reason}', message='{message}'")
        except AttributeError as e: messagebox.showerror("Game Error", f"Game logic missing 'check_game_over_status': {e}."); traceback.print_exc(); is_over, reason = True, "internal"
        except Exception as e: messagebox.showerror("Game Error", f"Error checking game over status: {e}"); traceback.print_exc(); is_over, reason = True, "internal"

        # --- Process Game Over State (Only Once) ---
        if is_over:
             # Backend should have set game_over_handled=True if is_over is True
             print("DEBUG GUI: Game over condition met.")
             self.disable_all_buttons() # Disable actions permanently

             # Ensure 'Next Round' button is removed
             if hasattr(self, 'next_round_button') and self.next_round_button and self.next_round_button.winfo_exists():
                  self.next_round_button.destroy(); delattr(self, 'next_round_button')

             log_message = message or "The game has ended."
             self.add_log_message(f"\n{'='*15} GAME OVER {'='*15}")
             self.add_log_message(log_message)

             # Trigger Specific Ending Based on Reason
             if reason in ["hearts", "busted"]: # Human lost
                 self.add_log_message("--- Your deal with the Devil concludes... ---")
                 self.root.after(1500, self.show_game_over_sequence) # Dramatic sequence
             elif reason in ["bot_bust", "chips"] and self.player_name in [n for n, p in self.game.players.items() if p['chips'] > 0]: # Player won
                 messagebox.showinfo("Game Over - You Win!", log_message)
                 self.add_log_message("--- YOU HAVE DEFIED THE DEVIL! (For now...) ---")
                 # Keep "Return to Menu" button active
             else: # Other reasons (error, no chips left, draw?)
                 messagebox.showinfo("Game Over", log_message)
                 self.add_log_message("--- THE HOUSE ALWAYS WINS... EVENTUALLY ---")
                 # Keep "Return to Menu" button active

        elif getattr(self.game, 'round_over', False):
             # Round ended, but game continues
             print("DEBUG GUI: check_game_over -> Round over, game continues. Calling prepare.")
             self.prepare_for_next_round_or_end()
        # else: Game and round continue (shouldn't happen right after winner determined)


    def show_game_over_sequence(self):
        """Displays the ending script in a dedicated frame when hearts run out."""
        if self.ending_frame and self.ending_frame.winfo_exists(): return # Already showing

        print("DEBUG GUI: Starting game over sequence.")
        # Hide Game UI
        if self.game_frame.winfo_ismapped(): self.game_frame.pack_forget()
        if self.log_frame.winfo_ismapped(): self.log_frame.pack_forget()

        # Create Ending Frame
        self.ending_frame = tk.Frame(self.root, bg="black")
        self.ending_frame.pack(fill=tk.BOTH, expand=True)

        # Create Text Widget
        self.ending_text_widget = Text(self.ending_frame, bg="black", fg="white", wrap=tk.WORD,
                                       padx=50, pady=50, bd=0, highlightthickness=0,
                                       font=self.SEQ_FONT_NORMAL, cursor="arrow") # No text cursor
        self.ending_text_widget.pack(fill=tk.BOTH, expand=True)
        self.ending_text_widget.config(state=tk.DISABLED) # Read-only

        # Configure Text Tags
        self.ending_text_widget.tag_configure("devil", foreground=self.SEQ_COLOR_DEVIL, font=self.SEQ_FONT_DEVIL)
        self.ending_text_widget.tag_configure("narrator", foreground=self.SEQ_COLOR_NARRATOR, font=self.SEQ_FONT_NORMAL, lmargin1=20, lmargin2=20) # Indent narration
        self.ending_text_widget.tag_configure("center", justify='center')
        self.ending_text_widget.tag_configure("prompt", foreground=self.SEQ_COLOR_DEFAULT, font=("Arial", 12, "italic"), justify='center')

        # *** NEW Game Over Script Lines ***
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

        self.ending_current_line = 0
        if self.ending_after_id:
            try:
                self.root.after_cancel(self.ending_after_id)
            except ValueError:
                pass
        self.ending_after_id = None
        self._display_next_ending_line()

        # Bind Events to Close Window
        self.root.bind("<KeyPress>", self._end_game_sequence_key)
        self.root.bind("<Button-1>", self._end_game_sequence_key) # Bind to root as well
        self.ending_frame.bind("<Button-1>", self._end_game_sequence_key)
        self.ending_text_widget.bind("<Button-1>", self._end_game_sequence_key)


    def _display_next_ending_line(self):
        """Internal method to display script lines sequentially."""
        if not self.ending_text_widget or not self.ending_text_widget.winfo_exists(): return
        if self.ending_current_line >= len(self.ending_script_lines): return

        line, tag, delay_ms = self.ending_script_lines[self.ending_current_line]
        try:
            self.ending_text_widget.config(state=tk.NORMAL)
            tags_to_apply = (tag,) if tag else ()
            if "center" in tags_to_apply or "prompt" in tags_to_apply: tags_to_apply += ("center",) # Ensure centering tag if needed
            self.ending_text_widget.insert(tk.END, line + "\n", tags_to_apply)
            self.ending_text_widget.see(tk.END)
            self.ending_text_widget.config(state=tk.DISABLED)
        except tk.TclError: print("Error: Ending text widget likely destroyed."); return

        self.ending_current_line += 1
        if delay_ms > 0 and self.ending_current_line < len(self.ending_script_lines):
            if self.ending_after_id:
                try:
                    self.root.after_cancel(self.ending_after_id)
                except ValueError: pass
            self.ending_after_id = self.root.after(delay_ms, self._display_next_ending_line)
        elif self.ending_current_line >= len(self.ending_script_lines):
             try: self.ending_text_widget.see(tk.END);
             except tk.TclError: pass; self.ending_after_id = None


    def _end_game_sequence_key(self, event=None):
        """Handles key press or click during the ending sequence to close the Poker window."""
        print("DEBUG GUI: _end_game_sequence_key triggered.")
        # Cancel pending text display
        if self.ending_after_id:
            try:
                self.root.after_cancel(self.ending_after_id)
            except ValueError: pass; self.ending_after_id = None
        # Unbind events
        try:
            self.root.unbind("<KeyPress>")
            self.root.unbind("<Button-1>")
            if self.ending_frame and self.ending_frame.winfo_exists(): self.ending_frame.unbind("<Button-1>")
            if self.ending_text_widget and self.ending_text_widget.winfo_exists(): self.ending_text_widget.unbind("<Button-1>")
        except tk.TclError: print("Warning: TclError during ending unbind."); pass
        # Close THIS Toplevel window using the callback
        self._return_to_menu(force_close=True) # Use return func, force close skips confirm


    # MODIFIED _return_to_menu
    def _return_to_menu(self, force_close=False):
        """Handles 'Return to Menu' button click or forced close: Confirms and calls the close callback."""
        confirmed = force_close # Skip confirmation if forced
        if not confirmed:
            # Add parent=self.root so the dialog appears over the poker window
            confirmed = messagebox.askokcancel("Return to Menu",
                                               "Leave the current game and return to the main menu?\nAny current game progress will be lost.",
                                               parent=self.root)

        if confirmed:
            self.add_log_message("--- Returning to Main Menu ---")
            try:
                # Cancel Pending Jobs safely (important!)
                if self.root.winfo_exists():
                    pending_jobs = self.root.tk.call('after', 'info')
                    for job_id in pending_jobs:
                        try: self.root.after_cancel(job_id)
                        except (tk.TclError, ValueError): pass # Ignore errors if job invalid/gone
                        except Exception as e_cancel: print(f"Warning: Error cancelling job {job_id}: {e_cancel}")

                # --- Call the callback function provided by MainMenu ---
                if self.on_close_callback:
                    print("PokerGUI: Calling on_close_callback...")
                    self.on_close_callback()
                else:
                    # Fallback if callback wasn't provided (shouldn't happen now)
                    print("PokerGUI ERROR: No on_close_callback available! Attempting direct destroy.")
                    if self.root.winfo_exists():
                        self.root.destroy()

            except tk.TclError:
                print("PokerGUI Warning: TclError during _return_to_menu cleanup (window likely closing).")
            except Exception as e:
                print(f"PokerGUI Error during _return_to_menu cleanup: {e}")
                traceback.print_exc()
            # NOTE: We no longer call self.root.destroy() here directly. The callback handles it.


# --- Main Execution Block (for standalone testing) ---
if __name__ == "__main__":
    print("Running PokerGUI directly for testing...")
    main_root = tk.Tk()
    # For standalone testing, create a dummy callback that just quits
    dummy_callback = lambda: main_root.quit()
    app = PokerGUI(main_root, on_close_callback=dummy_callback)
    main_root.protocol("WM_DELETE_WINDOW", dummy_callback)
    main_root.mainloop()
    print("PokerGUI standalone test finished.")