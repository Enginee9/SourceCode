import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, font, Text
import time
import random
import os

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Error", "Pillow library not found. Please install it: pip install Pillow")
    exit()

# --- Import Game Logic ---
try:
    from MatchManager_GUI import PokerGame, INITIAL_HEARTS
    from BotPlayer import BotPlayer
    from HandEvaluator import HandEvaluator
    from Deck import Deck
except ImportError as e:
     messagebox.showerror("Import Error", f"Failed to import game logic components: {e}\nMake sure MatchManager_GUI.py, BotPlayer.py, HandEvaluator.py, Deck.py are in the same directory.")
     exit()

class PokerGUI:
    # --- Constants ---
    CARD_WIDTH = 72
    CARD_HEIGHT = 100
    TABLE_GREEN = "#006400"
    HEART_ICON = "♥"
    SEQ_FONT_NORMAL = ("Arial", 16)
    SEQ_FONT_DEVIL = ("Arial", 18, "bold")
    SEQ_COLOR_DEVIL = "#FF4444"
    SEQ_COLOR_NARRATOR = "#CCCCCC"
    SEQ_COLOR_MAN = "#AAAAFF"
    SEQ_COLOR_DEFAULT = "#FFFFFF"
    STARTING_CHIPS = 1000

    def __init__(self, root):
        self.root = root
        self.root.title("Poker Game - Devil's Deal")
        self.root.geometry("1280x800")

        self.image_dir = "cards"
        self.card_images = {}
        self.card_back_image = None
        self._load_card_images()

        self.status_font = font.Font(family="Arial", size=12)
        self.heart_font = font.Font(family="Arial", size=14, weight="bold")
        self.log_font = font.Font(family="Consolas", size=9)

        self.game = None
        self.player_name = "Player"
        self.bot_count = 1
        self.bot_difficulty = "easy"
        # --- RE-ADD GUI Turn Tracking ---
        self.turn_order = []
        self.current_player_index = 0
        # --- End Re-add ---
        self.current_round_name = ""
        self.human_action_taken = False # Flag to prevent duplicate actions

        # --- UI Frames ---
        self.setup_frame = ttk.Frame(root, padding="10")
        self.game_frame = ttk.Frame(root, padding="10", style="Game.TFrame")
        self.log_frame = ttk.Frame(root, padding="5")
        self.ending_frame = None
        self.ending_text_widget = None
        self.ending_script_lines = []
        self.ending_current_line = 0
        self.ending_after_id = None

        # --- Style Configuration ---
        self.style = ttk.Style()
        self.style.configure("Game.TFrame", background=self.TABLE_GREEN)
        self.style.configure("GreenBG.TLabel", background=self.TABLE_GREEN, foreground="white")
        self.style.configure("GreenBG.TLabelframe", background=self.TABLE_GREEN)
        self.style.configure("GreenBG.TLabelframe.Label", background=self.TABLE_GREEN, foreground="white")
        self.style.configure("Hearts.TLabel", background=self.TABLE_GREEN, foreground="#FF6347", font=self.heart_font)

        # --- Log Area ---
        self.log_text = Text(self.log_frame, height=8, width=110, wrap=tk.WORD, font=self.log_font, relief=tk.SUNKEN, borderwidth=1, state=tk.DISABLED)
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=self.log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        # Place frames
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.setup_frame.pack(fill=tk.BOTH, expand=True)

        self._create_setup_widgets()
        self._create_game_widgets()

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._confirm_quit)

    # ... (_load_card_images, _create_setup_widgets, _create_game_widgets, _create_bot_area_placeholder) ...
    # ... (remain the same as previous correct version with Exit button) ...
    def _load_card_images(self):
        """Loads and resizes card images."""
        if not os.path.isdir(self.image_dir):
            messagebox.showerror("Error", f"Image directory '{self.image_dir}' not found.")
            self.root.quit(); return

        rank_map_file = {'A': 'ace', 'K': 'king', 'Q': 'queen', 'J': 'jack', 'T': '10', '9': '9', '8': '8', '7': '7', '6': '6', '5': '5', '4': '4', '3': '3', '2': '2'}
        suit_map_file = {'h': 'hearts', 'd': 'diamonds', 'c': 'clubs', 's': 'spades'}
        shorthand_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        shorthand_suits = ['h', 'd', 'c', 's']
        loaded_count = 0
        expected_count = len(shorthand_ranks) * len(shorthand_suits) + 1

        for rank_short in shorthand_ranks:
            for suit_short in shorthand_suits:
                card_shorthand = f"{rank_short}{suit_short}"
                rank_file = rank_map_file.get(rank_short)
                suit_file = suit_map_file.get(suit_short)
                if not rank_file or not suit_file: continue
                filename = f"{rank_file}_of_{suit_file}.jpg" # Ensure .jpg extension
                file_path = os.path.join(self.image_dir, filename)
                try:
                    img = Image.open(file_path).resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS)
                    self.card_images[card_shorthand] = ImageTk.PhotoImage(img)
                    loaded_count += 1
                except FileNotFoundError:
                    print(f"Warning: Image file not found: {file_path}")
                except Exception as e:
                    print(f"Warning: Failed to load/resize image {file_path}: {e}")

        card_back_path = os.path.join(self.image_dir, "card_back.jpg")
        try:
            img = Image.open(card_back_path).resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS)
            self.card_back_image = ImageTk.PhotoImage(img); loaded_count += 1
        except FileNotFoundError:
            print(f"Warning: Image file not found: {card_back_path}")
            messagebox.showwarning("Image Error", f"{card_back_path} not found. Hidden cards will be blank.")
        except Exception as e:
            print(f"Warning: Failed to load/resize image {card_back_path}: {e}")

        print(f"Loaded {loaded_count}/{expected_count} card images.")
        if loaded_count < expected_count:
             messagebox.showwarning("Image Load Warning", "Some card images failed to load. Check console and image folder.")


    def _create_setup_widgets(self):
        # (Setup widgets remain the same - no changes needed here)
        self.setup_frame.columnconfigure(0, weight=1); self.setup_frame.columnconfigure(1, weight=1)
        ttk.Label(self.setup_frame, text="Poker Setup - Devil's Deal", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(self.setup_frame, text="Your Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(self.setup_frame, width=30); self.name_entry.insert(0, self.player_name)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(self.setup_frame, text="Number of Bots:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.bot_count_var = tk.IntVar(value=1); bot_count_frame = ttk.Frame(self.setup_frame)
        for i in range(1, 4): ttk.Radiobutton(bot_count_frame, text=str(i), variable=self.bot_count_var, value=i).pack(side=tk.LEFT, padx=5)
        bot_count_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(self.setup_frame, text="Bot Difficulty:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.bot_difficulty_var = tk.StringVar(value="easy"); difficulty_frame = ttk.Frame(self.setup_frame)
        ttk.Radiobutton(difficulty_frame, text="Easy", variable=self.bot_difficulty_var, value="easy").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(difficulty_frame, text="Hard", variable=self.bot_difficulty_var, value="hard").pack(side=tk.LEFT, padx=5)
        difficulty_frame.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.start_button = ttk.Button(self.setup_frame, text="Make the Deal", command=self.start_game)
        self.start_button.grid(row=4, column=0, columnspan=2, pady=20)

    def _create_game_widgets(self):
        # --- Grid Config ---
        self.game_frame.columnconfigure(0, weight=1); self.game_frame.columnconfigure(1, weight=1); self.game_frame.columnconfigure(2, weight=1)
        self.game_frame.rowconfigure(0, weight=1) # Bot row 1
        self.game_frame.rowconfigure(1, weight=1) # Bot row 2 / Center Info
        self.game_frame.rowconfigure(2, weight=1) # Player Area Row
        self.game_frame.rowconfigure(3, weight=0) # Exit button row (minimal weight)

        # --- Community Card Area ---
        community_frame = ttk.LabelFrame(self.game_frame, text="Community Cards", padding="5", style="GreenBG.TLabelframe")
        community_frame.grid(row=0, column=1, rowspan=2, pady=5, sticky="nsew") # Span rows 0 and 1
        self.community_card_labels = []
        card_area_frame = ttk.Frame(community_frame, style="Game.TFrame") # Inner frame for centering
        card_area_frame.pack(expand=True) # Center the card frame itself
        for i in range(5):
            lbl = ttk.Label(card_area_frame, image=self.card_back_image, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = self.card_back_image; lbl.pack(side=tk.LEFT, padx=3); self.community_card_labels.append(lbl)


        # --- Pot and Bet Info Area ---
        info_frame = ttk.Frame(self.game_frame, padding="5", style="Game.TFrame")
        # Place it slightly lower, perhaps row 1, column 1? Or adjust community cards row span
        info_frame.grid(row=1, column=1, pady=5, sticky="s") # Stick to south of its cell
        info_frame.columnconfigure(0, weight=1)
        self.pot_label = ttk.Label(info_frame, text="Pot: 0", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.pot_label.grid(row=0, column=0, pady=1, sticky="ew")
        self.current_bet_label = ttk.Label(info_frame, text="Current Bet: 0", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.current_bet_label.grid(row=1, column=0, pady=1, sticky="ew")
        self.current_turn_label = ttk.Label(info_frame, text="Turn: -", font=self.status_font, anchor="center", style="GreenBG.TLabel")
        self.current_turn_label.grid(row=2, column=0, pady=1, sticky="ew")

        # --- Player Area (Row 2) ---
        player_frame = ttk.LabelFrame(self.game_frame, text="You", padding="10", style="GreenBG.TLabelframe")
        player_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="nsew")
        player_frame.columnconfigure(0, weight=1); player_frame.columnconfigure(1, weight=1); player_frame.columnconfigure(2, weight=1)

        # Player Stats
        player_stats_frame = ttk.Frame(player_frame, style="Game.TFrame")
        player_stats_frame.grid(row=0, column=0, sticky="nw", padx=10)
        self.player_chips_label = ttk.Label(player_stats_frame, text=f"Chips: {self.STARTING_CHIPS}", font=self.status_font, style="GreenBG.TLabel")
        self.player_chips_label.pack(anchor="w", pady=2)
        self.player_hearts_label = ttk.Label(player_stats_frame, text=f"Hearts: {self.HEART_ICON * INITIAL_HEARTS}", style="Hearts.TLabel")
        self.player_hearts_label.pack(anchor="w", pady=2)

        # Player Cards
        cards_frame = ttk.Frame(player_frame, style="Game.TFrame")
        cards_frame.grid(row=0, column=1, pady=5, sticky="n")
        self.player_card_labels = []
        for i in range(2):
            lbl = ttk.Label(cards_frame, image=self.card_back_image, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = self.card_back_image; lbl.pack(side=tk.LEFT, padx=5); self.player_card_labels.append(lbl)

        # Action Buttons
        action_frame = ttk.Frame(player_frame, style="Game.TFrame")
        action_frame.grid(row=0, column=2, padx=10, sticky="ne")
        self.check_button = ttk.Button(action_frame, text="Check", command=lambda: self.handle_human_action("check", 0), state=tk.DISABLED)
        self.check_button.pack(pady=2, fill=tk.X)
        self.call_button = ttk.Button(action_frame, text="Call", command=lambda: self.handle_human_action("call", 0), state=tk.DISABLED)
        self.call_button.pack(pady=2, fill=tk.X)
        self.fold_button = ttk.Button(action_frame, text="Fold", command=lambda: self.handle_human_action("fold", 0), state=tk.DISABLED)
        self.fold_button.pack(pady=2, fill=tk.X)
        raise_frame = ttk.Frame(action_frame, style="Game.TFrame")
        raise_frame.pack(pady=2, fill=tk.X)
        self.raise_button = ttk.Button(raise_frame, text="Raise", command=self.handle_raise_prompt, state=tk.DISABLED)
        self.raise_button.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.raise_amount_var = tk.StringVar()
        self.raise_entry = ttk.Entry(raise_frame, width=7, textvariable=self.raise_amount_var, state=tk.DISABLED)
        self.raise_entry.pack(side=tk.LEFT, padx=(3,0))
        self.all_in_button = ttk.Button(action_frame, text="All In", command=lambda: self.handle_human_action("all in", 0), state=tk.DISABLED)
        self.all_in_button.pack(pady=2, fill=tk.X)

        # --- Bot Areas ---
        self.bot_widgets = {}
        self._create_bot_area_placeholder("Bot_1", 0, 0) # Top Left
        self._create_bot_area_placeholder("Bot_2", 0, 2) # Top Right
        self._create_bot_area_placeholder("Bot_3", 1, 0) # Mid Left

        # --- Exit Button (Row 3) ---
        self.exit_button = ttk.Button(self.game_frame, text="Exit Game", command=self._confirm_quit)
        self.exit_button.grid(row=3, column=0, padx=10, pady=10, sticky="sw") # Bottom-left corner


    def _create_bot_area_placeholder(self, placeholder_name, grid_row, grid_col):
        """Creates the widgets for a bot area but doesn't grid it yet."""
        frame = ttk.LabelFrame(self.game_frame, text=placeholder_name, padding="5", style="GreenBG.TLabelframe")
        info_label = ttk.Label(frame, text=f"Chips: {self.STARTING_CHIPS}", font=self.status_font, anchor="w", style="GreenBG.TLabel")
        info_label.pack(pady=2, fill=tk.X)
        status_label = ttk.Label(frame, text="Status: Waiting", font=self.status_font, anchor="w", style="GreenBG.TLabel")
        status_label.pack(pady=2, fill=tk.X)
        cards_frame = ttk.Frame(frame, style="Game.TFrame"); cards_frame.pack(pady=5)
        card_labels = []
        for i in range(2):
            lbl = ttk.Label(cards_frame, image=self.card_back_image, relief=tk.GROOVE, borderwidth=1, anchor="center")
            lbl.image = self.card_back_image; lbl.pack(side=tk.LEFT, padx=3); card_labels.append(lbl)
        # Store placeholder info, grid row/col will be used by _configure_bot_displays
        self.bot_widgets[placeholder_name] = {
            'frame': frame, 'info_label': info_label, 'status_label': status_label,
            'card_labels': card_labels, 'intended_row': grid_row, 'intended_col': grid_col
        }


    def add_log_message(self, message):
        """Appends a message to the log area."""
        if self.log_text:
            try:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except tk.TclError:
                print("Log widget error (likely closing):", message)

    def start_game(self):
        """Initializes the game logic via constructor and switches to the game view."""
        self.player_name = self.name_entry.get() or "Player"
        self.bot_count = self.bot_count_var.get()
        self.bot_difficulty = self.bot_difficulty_var.get()

        self.game = None # Reset game object
        try:
            # --- Create Game Instance using Constructor ---
            print(f"DEBUG GUI: Creating PokerGame with P:{self.player_name}, B:{self.bot_count}, D:{self.bot_difficulty}, H:{INITIAL_HEARTS}, C:{self.STARTING_CHIPS}")
            self.game = PokerGame(
                player_name=self.player_name,
                bot_count=self.bot_count,
                bot_difficulty=self.bot_difficulty,
                initial_hearts=INITIAL_HEARTS,
                initial_chips=self.STARTING_CHIPS # Pass starting chips here
            )
            # No separate setup_game_gui call needed

        except NameError as e:
             messagebox.showerror("Setup Error", f"A required name is not defined (check imports/constants): {e}")
             import traceback; traceback.print_exc()
             self.game = None; return
        except TypeError as e:
             messagebox.showerror("Setup Error", f"Mismatch in arguments for PokerGame setup: {e}\nCheck PokerGame.__init__ in MatchManager_GUI.py.")
             import traceback; traceback.print_exc()
             self.game = None; return
        except Exception as e:
            messagebox.showerror("Setup Error", f"Failed to set up game: {e}")
            import traceback; traceback.print_exc()
            self.game = None; return

        self._configure_bot_displays() # Place bot widgets correctly

        self.setup_frame.pack_forget()
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.add_log_message(f"--- Game Started - {self.player_name} vs {self.bot_count} Bot(s) ---")
        self.add_log_message(f"Starting with {self.STARTING_CHIPS} chips and {INITIAL_HEARTS} hearts.")
        self.add_log_message("Don't lose your hearts!")

        self.start_new_round()


    def _configure_bot_displays(self):
        """Grids the bot frames correctly based on the number of bots."""
        # Hide all first
        for widgets in self.bot_widgets.values():
             widgets['frame'].grid_forget()

        if not self.game: return
        # Get actual bot names from the game instance's list of bot objects or player dict
        bot_names_in_game = []
        if hasattr(self.game, 'bots') and self.game.bots:
            bot_names_in_game = [b.name for b in self.game.bots]
        elif hasattr(self.game, 'players'): # Fallback: get from players dict if 'is_bot' exists
            bot_names_in_game = [name for name, p in self.game.players.items() if p.get('is_bot')]

        if not bot_names_in_game:
             print("DEBUG GUI: No bot names found in game instance for display configuration.")
             return

        # Map actual bot names to placeholder widgets based on intended positions
        placeholder_keys = list(self.bot_widgets.keys()) # Bot_1, Bot_2, Bot_3

        for i, actual_bot_name in enumerate(bot_names_in_game):
            if i < len(placeholder_keys):
                 placeholder_key = placeholder_keys[i]
                 widgets_to_place = self.bot_widgets[placeholder_key]
                 grid_row = widgets_to_place['intended_row']
                 grid_col = widgets_to_place['intended_col']

                 widgets_to_place['frame'].config(text=actual_bot_name) # Set the actual name
                 widgets_to_place['frame'].grid(row=grid_row, column=grid_col, padx=5, pady=5, sticky="nsew")
                 print(f"DEBUG GUI: Placed bot '{actual_bot_name}' at grid ({grid_row},{grid_col}) using placeholder {placeholder_key}")
            else:
                 print(f"Warning: More bots ({len(bot_names_in_game)}) than defined placeholders ({len(placeholder_keys)}). Bot '{actual_bot_name}' not displayed.")
                 break


    def start_new_round(self):
        """Tells backend to start a new round and updates UI."""
        if not self.game: return
        # Check if game ended before starting
        is_over, _, _ = self.game.check_game_over_status()
        if is_over:
            self.check_game_over()
            return

        self.add_log_message("\n--- Starting New Round ---")
        try:
            round_info = self.game.start_new_round_get_info()
            if not round_info or 'error' in round_info:
                err_msg = round_info.get('error', 'Unknown error starting round.') if round_info else 'No round info returned.'
                messagebox.showerror("Round Error", err_msg)
                if round_info and round_info.get('game_over'): self.game.game_over = True
                else: self.game.game_over = True
                self.check_game_over(); return

            # --- Get turn order from backend ---
            self.turn_order = round_info.get('turn_order', []) # Store turn order locally
            self.current_player_index = round_info.get('start_index', -1) # Store start index
            # ---

            dealer_name = round_info.get('dealer', '-')
            sb_player = round_info.get('sb_player', '?')
            sb_amount = round_info.get('sb_amount', '?')
            bb_player = round_info.get('bb_player', '?')
            bb_amount = round_info.get('bb_amount', '?')

            if not self.turn_order or self.current_player_index < 0:
                 print("Warning GUI: StartNewRound returned invalid turn order/start index.")
                 self.current_round_name = self.game.current_stage if self.game else "N/A"
                 self.update_ui()
                 # If no turn order, maybe betting is over immediately? Or stage advance needed?
                 self.root.after(100, self.process_next_turn) # Let process_next_turn figure it out
                 return

            self.add_log_message(f"Dealer button is on {dealer_name}.")
            self.add_log_message(f"{sb_player} posts small blind {sb_amount}.")
            self.add_log_message(f"{bb_player} posts big blind {bb_amount}.")

            self.current_round_name = self.game.current_stage
            self.update_ui()
            # Trigger the first turn check
            self.root.after(100, self.process_next_turn)

        except AttributeError as e:
            messagebox.showerror("Round Error", f"Game logic error (missing method/attribute): {e}")
            import traceback; traceback.print_exc()
            if self.game: self.game.game_over = True
            self.check_game_over()
        except Exception as e:
            messagebox.showerror("Round Error", f"Failed to start round: {e}")
            import traceback; traceback.print_exc()
            if self.game: self.game.game_over = True
            self.check_game_over()

    def update_ui(self, show_bot_cards=False):
        """Updates all GUI elements based on the current game state."""
        if not self.game or not self.card_images: return

        try:
            state = self.game.get_game_state_summary()
            if not state or 'players' not in state:
                 print("Error: Invalid game state received in update_ui.")
                 return

            # Pot, Bet, Turn labels
            self.pot_label.config(text=f"Pot: {state.get('pot', 'N/A')}")
            self.current_bet_label.config(text=f"Current Bet: {state.get('current_bet', 'N/A')}")

            # --- Get Current Player Reliably from Backend ---
            current_player_name = state.get('current_turn_player', "-")
            self.current_turn_label.config(text=f"Turn: {current_player_name}")
            # Update internal stage name display
            self.current_round_name = state.get('current_stage', self.current_round_name)

            # Community Cards
            cc = state.get('community_cards', [])
            for i, lbl in enumerate(self.community_card_labels):
                img = self.card_back_image
                if i < len(cc) and cc[i]:
                     img = self.card_images.get(cc[i], self.card_back_image)
                lbl.config(image=img if img else self.card_back_image)
                lbl.image = img if img else self.card_back_image

            # Player Info and Cards
            player_state = state['players'].get(self.player_name)
            if player_state:
                status_text = ""
                if player_state.get('folded'): status_text = " (Folded)"
                if player_state.get('all_in'): status_text = " (ALL IN)"
                self.player_chips_label.config(text=f"Chips: {player_state.get('chips', 0)}{status_text}")
                hearts = player_state.get('hearts', 0)
                self.player_hearts_label.config(text=f"Hearts: {self.HEART_ICON * hearts}")
                pc = player_state.get('cards', [])
                for i, lbl in enumerate(self.player_card_labels):
                    img = self.card_back_image
                    if i < len(pc) and pc[i]: img = self.card_images.get(pc[i], self.card_back_image)
                    lbl.config(image=img if img else self.card_back_image)
                    lbl.image = img if img else self.card_back_image
            else:
                 self.player_chips_label.config(text="Chips: -"); self.player_hearts_label.config(text="Hearts: -")

            # Bot Info and Cards
            bot_names_in_game = [name for name, p in state['players'].items() if p.get('is_bot')]
            placeholder_keys = list(self.bot_widgets.keys())
            for i, actual_bot_name in enumerate(bot_names_in_game):
                 if i < len(placeholder_keys):
                      placeholder_key = placeholder_keys[i]
                      widgets = self.bot_widgets[placeholder_key]
                      bot_state = state['players'].get(actual_bot_name)
                      if bot_state:
                            status_text = "Active"
                            if bot_state.get('folded'): status_text = "Folded"
                            if bot_state.get('all_in'): status_text = "ALL IN"
                            widgets['info_label'].config(text=f"Chips: {bot_state.get('chips', 0)}")
                            widgets['status_label'].config(text=f"Status: {status_text}")
                            bc = bot_state.get('cards', [])
                            for j, lbl in enumerate(widgets['card_labels']):
                                 img = self.card_back_image
                                 if j < len(bc) and bc[j] and (show_bot_cards or self.current_round_name == "showdown"):
                                     img = self.card_images.get(bc[j], self.card_back_image)
                                 lbl.config(image=img if img else self.card_back_image)
                                 lbl.image = img if img else self.card_back_image
                      else: widgets['info_label'].config(text="Chips: -"); widgets['status_label'].config(text="Status: Unknown")

            # --- Enable/Disable Buttons based *directly* on backend state ---
            # Only enable if backend says it's human turn AND game/round not over AND player is eligible
            if current_player_name == self.player_name and \
               not getattr(self.game, 'round_over', False) and \
               not getattr(self.game, 'game_over', False):

                player_state_now = self.game.players.get(self.player_name) # Check internal state
                if player_state_now and not player_state_now.get('folded') and not player_state_now.get('all_in'):
                     print(f"DEBUG GUI: Enabling buttons for {self.player_name}")
                     self.update_action_buttons()
                else:
                     print(f"DEBUG GUI: Disabling buttons for {self.player_name} (Backend state: Folded/AllIn)")
                     self.disable_all_buttons()
            else:
                self.disable_all_buttons()

        except tk.TclError as e: print(f"TclError during UI update: {e}")
        except AttributeError as e: print(f"AttributeError during UI update: {e}"); import traceback; traceback.print_exc()
        except Exception as e: messagebox.showerror("UI Update Error", f"Error during UI update: {e}"); import traceback; traceback.print_exc()


    # ... (update_action_buttons, disable_all_buttons remain the same) ...
    def update_action_buttons(self):
        """Enables/disables action buttons based on game state and player turn."""
        state = self.game.get_game_state_summary()
        player_state = state['players'].get(self.player_name)
        if not player_state or player_state.get('folded') or player_state.get('all_in'):
             self.disable_all_buttons(); return

        chips = player_state.get('chips', 0)
        current_bet = state.get('current_bet', 0)
        player_bet_this_round = player_state.get('current_round_bet', 0)
        amount_to_call = max(0, current_bet - player_bet_this_round)
        # Use big blind from game logic if available, else fallback
        big_blind = getattr(self.game, 'big_blind', 20) # Example fallback
        previous_bet = state.get('previous_bet', 0)

        # Fold Button
        self.fold_button.config(state=tk.NORMAL)

        # Check / Call Buttons
        can_check = amount_to_call <= 0
        self.check_button.config(state=tk.NORMAL if can_check else tk.DISABLED)

        if not can_check: # Needs to call or fold
             if chips >= amount_to_call: # Can afford full call
                 self.call_button.config(state=tk.NORMAL, text=f"Call {amount_to_call}")
             else: # Can only call by going all-in
                 self.call_button.config(state=tk.NORMAL, text=f"Call {chips} (All In)")
        else: # Check is available
            self.call_button.config(state=tk.DISABLED, text="Call")

        # Raise / All-in Buttons
        can_raise = chips > amount_to_call # Can potentially raise if chips > amount needed to call

        if can_raise:
            # Min raise increment: larger of BB or the previous raise amount
            min_raise_increment = max(big_blind, current_bet - previous_bet if current_bet > previous_bet else big_blind)
            # Min total bet player must make if they raise
            min_legal_total_bet_target = current_bet + min_raise_increment
            # Calculate minimum *additional* chips needed for this minimum raise
            min_additional_chips_needed = max(1, min_legal_total_bet_target - player_bet_this_round)

            # Can player afford the minimum *additional* chips?
            if chips >= amount_to_call + min_additional_chips_needed:
                 self.raise_button.config(state=tk.NORMAL, text=f"Raise (Min +{min_additional_chips_needed})")
                 self.raise_entry.config(state=tk.NORMAL)
            else: # Cannot afford minimum raise, only all-in is possible beyond call
                 self.raise_button.config(state=tk.DISABLED, text="Raise")
                 self.raise_entry.config(state=tk.DISABLED); self.raise_amount_var.set("")
        else: # Cannot raise (chips <= amount_to_call)
            self.raise_button.config(state=tk.DISABLED, text="Raise")
            self.raise_entry.config(state=tk.DISABLED); self.raise_amount_var.set("")

        # All-in button enabled if chips > 0
        if chips > 0:
            self.all_in_button.config(state=tk.NORMAL, text=f"All In ({chips})")
        else:
             self.all_in_button.config(state=tk.DISABLED, text="All In")


    def disable_all_buttons(self):
        """Disables all player action buttons."""
        self.check_button.config(state=tk.DISABLED)
        self.call_button.config(state=tk.DISABLED, text="Call")
        self.fold_button.config(state=tk.DISABLED)
        self.raise_button.config(state=tk.DISABLED, text="Raise")
        self.raise_entry.config(state=tk.DISABLED); self.raise_amount_var.set("")
        self.all_in_button.config(state=tk.DISABLED, text="All In")


    def handle_human_action(self, action, total_bet_amount=0):
        """Processes the human player's chosen action."""
        if not self.game or self.game.game_over or self.game.round_over: return
        if self.human_action_taken: return # Prevent double clicks

        # --- CRITICAL CHECK: Verify turn with backend ---
        try:
            backend_turn = self.game.get_game_state_summary().get('current_turn_player')
            if backend_turn != self.player_name:
                 print(f"ERROR GUI: handle_human_action called for {self.player_name} but backend turn is {backend_turn}. Ignoring.")
                 return
        except Exception as e: print(f"ERROR GUI: Failed verify turn in handle_human_action: {e}"); return
        # --- End Check ---

        self.human_action_taken = True
        self.disable_all_buttons()

        state = self.game.get_game_state_summary() # Get fresh state
        player_state = state['players'].get(self.player_name)
        if not player_state: self.human_action_taken = False; return

        chips = player_state.get('chips', 0)
        player_bet_this_round = player_state.get('current_round_bet', 0)
        final_total_round_bet = player_bet_this_round
        action_log = action.capitalize()
        processed_action = action

        try:
            # ... (action amount/log calculation logic remains the same) ...
            if action == "call":
                current_bet = state.get('current_bet', 0) # Use current bet from state
                amount_to_call = max(0, current_bet - player_bet_this_round)
                call_chip_cost = min(amount_to_call, chips)
                final_total_round_bet = player_bet_this_round + call_chip_cost
                is_all_in_call = (call_chip_cost == chips) and chips > 0 and amount_to_call > 0
                action_log = f"Call {call_chip_cost}" + (" (All In)" if is_all_in_call else "")
                if is_all_in_call : processed_action = "all in"
            elif action == "all in":
                final_total_round_bet = player_bet_this_round + chips
                action_log = f"All In ({chips})"
                processed_action = "all in"
            elif action == "raise":
                final_total_round_bet = total_bet_amount # Assumed pre-validated
                raise_increment = final_total_round_bet - player_bet_this_round
                is_all_in_raise = (raise_increment >= chips) and chips > 0 # >= because raise_increment might exceed chips
                action_log = f"Raise to {final_total_round_bet} (+{raise_increment})" + (" (All In)" if is_all_in_raise else "")
                if is_all_in_raise : processed_action = "all in"
            elif action == "check": action_log = "Check"
            elif action == "fold": action_log = "Fold"


            self.add_log_message(f"{self.player_name}: {action_log}")
            self.game.process_player_action(self.player_name, processed_action, final_total_round_bet)
            self.update_ui()
            self.root.update()
            # --- Trigger the next turn check ---
            self.root.after(150, self.process_next_turn) # Use process_next_turn

        except ValueError as e:
            messagebox.showerror("Action Error", str(e))
            self.update_ui() # Re-enable buttons if still player's turn
            self.human_action_taken = False # Allow action again
        except Exception as e:
            messagebox.showerror("Game Error", f"Error processing action: {e}")
            import traceback; traceback.print_exc()
            if self.game: self.game.game_over = True
            self.check_game_over()
            self.human_action_taken = False # Reset on major error


    # ... (handle_raise_prompt remains the same) ...
    def handle_raise_prompt(self):
        """Handles the raise action, prompting for amount."""
        if not self.game: return
        state = self.game.get_game_state_summary()
        player_state = state['players'].get(self.player_name)
        if not player_state: return

        chips = player_state.get('chips', 0)
        current_bet = state.get('current_bet', 0)
        player_bet_this_round = player_state.get('current_round_bet', 0)
        previous_bet = state.get('previous_bet', 0)
        big_blind = getattr(self.game, 'big_blind', 20) # Fallback BB
        amount_to_call = max(0, current_bet - player_bet_this_round)

        # Min Raise calculation (total bet target)
        min_raise_increment = max(big_blind, current_bet - previous_bet if current_bet > previous_bet else big_blind)
        min_legal_total_bet_target = current_bet + min_raise_increment
        # Max possible raise (all-in total bet)
        max_possible_total_bet = player_bet_this_round + chips
        # Actual minimum player can raise to (capped by all-in)
        min_player_can_raise_to = min(min_legal_total_bet_target, max_possible_total_bet)
        # Smallest *additional* amount needed for the minimum valid raise
        # Ensure min_additional is at least 1 if any raise is possible
        if min_player_can_raise_to > player_bet_this_round:
             min_additional_chips_needed = max(1, min_player_can_raise_to - player_bet_this_round)
        else: # Cannot even raise by 1 chip
             min_additional_chips_needed = 0


        # Check if ANY raise is possible
        can_afford_min_raise = chips >= amount_to_call + min_additional_chips_needed if min_additional_chips_needed > 0 else False
        if chips <= amount_to_call or not can_afford_min_raise :
             messagebox.showinfo("Raise Info", "Not enough chips to make a valid raise.")
             return

        target_total_bet_str = self.raise_amount_var.get()
        try:
            target_total_bet = 0
            if target_total_bet_str:
                 target_total_bet = int(target_total_bet_str)
                 # Validate entry
                 if not (min_player_can_raise_to <= target_total_bet <= max_possible_total_bet):
                      messagebox.showwarning("Invalid Raise Amount", f"Total bet must be between {min_player_can_raise_to} and {max_possible_total_bet}.")
                      self.raise_amount_var.set(str(min_player_can_raise_to))
                      return
            else:
                # Prompt for the TOTAL bet amount
                prompt_val = simpledialog.askinteger("Raise To",
                                                 f"Enter TOTAL bet amount for this round.\n"
                                                 f"(Current bet: {current_bet}, You've bet: {player_bet_this_round})\n"
                                                 f"Min Total Bet: {min_player_can_raise_to} (+{min_additional_chips_needed} chips)\n"
                                                 f"Max Total Bet (All In): {max_possible_total_bet}",
                                                 parent=self.root,
                                                 initialvalue=min_player_can_raise_to,
                                                 minvalue=min_player_can_raise_to,
                                                 maxvalue=max_possible_total_bet)
                if prompt_val is None: return # User cancelled
                target_total_bet = prompt_val

            # Final validation (redundant for dialog but good safety)
            if not (min_player_can_raise_to <= target_total_bet <= max_possible_total_bet):
                 messagebox.showwarning("Invalid Raise", f"Total bet must be between {min_player_can_raise_to} and {max_possible_total_bet}.")
                 return

            self.handle_human_action("raise", target_total_bet)

        except ValueError: messagebox.showwarning("Invalid Input","Please enter a valid number.")
        except Exception as e: messagebox.showerror("Error", f"Raise error: {e}"); import traceback; traceback.print_exc()


    def process_next_turn(self):
        """Determines the next action based on game state (human wait or bot action)."""
        print(f"DEBUG GUI: process_next_turn triggered.")
        if not self.game or self.game.game_over:
            self.check_game_over(); return
        if self.game.round_over:
            print("DEBUG GUI: process_next_turn found round_over = True")
            self.root.after(100, self.check_game_over) # Check winner/game over
            return

        # --- Get current state from backend ---
        try:
            state = self.game.get_game_state_summary()
            is_betting_over = self.game.is_betting_over() # Check if backend thinks betting is done
            current_player_name = state.get('current_turn_player')
            self.current_round_name = state.get('current_stage', self.current_round_name) # Update stage display
            print(f"DEBUG GUI: process_next_turn - Backend state: Turn={current_player_name}, BettingOver={is_betting_over}, Stage={self.current_round_name}")

        except Exception as e:
             messagebox.showerror("Game State Error", f"Failed to get/process game state: {e}")
             if self.game: self.game.game_over = True
             self.check_game_over(); return

        # --- Decide next step ---
        if is_betting_over:
            print(f"DEBUG GUI: Betting is over for {self.current_round_name}. Advancing stage.")
            self.update_ui() # Show final bets for stage
            self.root.after(200, self.advance_game_stage)

        elif current_player_name is None:
             print("ERROR GUI: Backend reported betting not over, but no current player specified!")
             # Try advancing stage as fallback? Could be everyone all-in.
             self.root.after(100, self.advance_game_stage)

        elif current_player_name == self.player_name:
             # It's human's turn. Update UI (which should enable buttons).
             print(f"DEBUG GUI: Waiting for human player ({self.player_name}) action.")
             self.human_action_taken = False # Reset flag, allow action
             self.update_ui()
             # Optionally add log message here
             # self.add_log_message(f"--- Your Turn ({self.current_round_name}) ---")

        else: # It's a bot's turn
             print(f"DEBUG GUI: Triggering action for bot: {current_player_name}")
             self.update_ui() # Update UI to show it's bot's turn (buttons disabled)
             # Optionally add log message here
             # self.add_log_message(f"--- {current_player_name}'s Turn ({self.current_round_name}) ---")
             self.root.update() # Ensure UI update appears
             think_time = random.randint(500, 1300)
             # Schedule the bot action call
             self.root.after(think_time, self.get_bot_action, current_player_name)


    # ... (get_bot_action uses process_next_turn at the end) ...
    def get_bot_action(self, bot_name):
        """Gets and processes the bot's action from the game logic."""
        if not self.game or self.game.round_over or self.game.game_over: return

        # Optional check: Verify backend agrees it's this bot's turn
        try:
            backend_turn = self.game.get_game_state_summary().get('current_turn_player')
            if backend_turn != bot_name:
                print(f"ERROR GUI: get_bot_action called for {bot_name} but backend turn is {backend_turn}. Triggering next turn check.")
                self.root.after(50, self.process_next_turn)
                return
        except Exception as e:
             print(f"ERROR GUI: Failed to verify turn with backend in get_bot_action: {e}")
             pass # Proceed cautiously

        try:
            action, total_bet_amount = self.game.get_bot_action_gui(bot_name)
            player_state = self.game.players[bot_name]
            chips = player_state.get('chips', 0)
            player_bet_this_round = player_state.get('current_round_bet', 0)
            action_log = action.capitalize()
            processed_action = action
            final_total_round_bet = 0

            # ... (Refine logging/processed_action - same as before) ...
            if action == "call":
                amount_to_call = self.game.current_bet - player_bet_this_round
                call_chip_cost = min(amount_to_call, chips) if amount_to_call > 0 else 0
                is_all_in = (call_chip_cost == chips) and chips > 0 and amount_to_call > 0
                action_log = f"Call {call_chip_cost}" + (" (All In)" if is_all_in else "")
                if is_all_in: processed_action = "all in"
                final_total_round_bet = player_bet_this_round + call_chip_cost
            elif action == "raise":
                raise_increment = total_bet_amount - player_bet_this_round
                is_all_in = (raise_increment >= chips) and chips > 0 # Use >= if raise cost might exceed chips
                action_log = f"Raise to {total_bet_amount} (+{raise_increment})" + (" (All In)" if is_all_in else "")
                if is_all_in: processed_action = "all in"
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
                 final_total_round_bet = player_bet_this_round

            self.add_log_message(f"{bot_name}: {action_log}")
            self.game.process_player_action(bot_name, processed_action, final_total_round_bet)
            self.update_ui()
            self.root.update()
            # --- Trigger process_next_turn ---
            self.root.after(150, self.process_next_turn)

        except Exception as e: # Catch errors broadly here
             messagebox.showerror("Bot Action Error", f"Error during {bot_name}'s turn: {e}")
             import traceback; traceback.print_exc()
             try: # Attempt to fold bot on error
                 self.add_log_message(f"Error for {bot_name}, folding.")
                 if self.game: self.game.process_player_action(bot_name, "fold", 0)
                 self.update_ui()
                 self.root.after(150, self.process_next_turn) # Still trigger next turn check
             except Exception as fold_e:
                 print(f"ERROR GUI: Failed to fold bot {bot_name} after error: {fold_e}")
                 if self.game: self.game.game_over = True
                 self.check_game_over()


    # --- REMOVE the advance_turn method ---


    # ... (advance_game_stage, determine_winner_and_proceed, display_winner) ...
    # ... (prepare_for_next_round_or_end, click_next_round) ...
    # ... (check_game_over, show_game_over_sequence, _display_next_ending_line, _end_game_sequence_key) ...
    # ... (_confirm_quit, _quit_game) ...
    # ... (remain the same as the previous version) ...
    def advance_game_stage(self):
         """Tells the game logic to advance (deal flop/turn/river/showdown) and updates UI."""
         print(f"DEBUG GUI: advance_game_stage called. Current stage was: {self.current_round_name}")
         if not self.game or self.game.game_over:
              self.check_game_over(); return

         # Check for premature round end (only 1 player left not folded)
         # This check should ideally happen within MatchManager, but we can double-check
         state = self.game.get_game_state_summary()
         active_players = [p for p in state['players'].values() if not p.get('folded')]
         if len(active_players) <= 1 and not self.game.round_over:
              self.game.round_over = True # Mark round over
              self.add_log_message("\n--- Round End (Only one active player left) ---")
              print("DEBUG GUI: advance_game_stage -> Round ended early (one player).")
              self.update_ui(show_bot_cards=True)
              self.root.after(100, self.determine_winner_and_proceed) # Go to winner display/check over
              return

         # --- Ask MatchManager_GUI to advance its internal stage ---
         try:
             next_stage = self.game.advance_to_next_stage()
             print(f"DEBUG GUI: game.advance_to_next_stage() returned: {next_stage}")
             if self.game: # Check if game object still exists after call
                self.current_round_name = self.game.current_stage # Update GUI's stage name
         except AttributeError:
             messagebox.showerror("Game Error", "Game logic missing 'advance_to_next_stage' method.")
             if self.game: self.game.game_over = True
             self.check_game_over(); return
         except Exception as e:
              messagebox.showerror("Stage Error", f"Error advancing game stage logic: {e}")
              import traceback; traceback.print_exc()
              if self.game: self.game.game_over = True
              self.check_game_over(); return

         # --- Process the result of advancing the stage ---
         if next_stage == "showdown":
             self.add_log_message("\n--- Showdown ---")
             self.update_ui(show_bot_cards=True) # Reveal all cards
             self.root.update() # Show cards before winner display
             self.root.after(100, self.determine_winner_and_proceed)

         elif next_stage: # Flop, Turn, River successfully dealt
             self.add_log_message(f"\n--- Dealing {next_stage.capitalize()} ---")

             # Start the betting round for the new stage
             try:
                round_info = self.game.start_next_betting_round()
                # Get the turn order info but GUI doesn't need to store it long term
                gui_turn_order = round_info.get('turn_order', [])
                gui_start_index = round_info.get('start_index', -1)
                print(f"DEBUG GUI: New betting round ({next_stage}). Turn order: {gui_turn_order}, Start index: {gui_start_index}")

                # Handle case where betting is immediately over (e.g., all remaining players all-in)
                if not gui_turn_order or gui_start_index < 0:
                     print(f"DEBUG GUI: Betting skipped for {next_stage} (no actors or all-in).")
                     self.update_ui() # Update to show new cards
                     self.root.after(500, self.advance_game_stage) # Advance again quickly
                     return # Skip calling process_next_turn

             except AttributeError:
                 messagebox.showerror("Game Error", "Game logic missing 'start_next_betting_round' method.")
                 self.game.game_over = True; self.check_game_over(); return
             except Exception as e:
                 messagebox.showerror("Betting Round Error", f"Error starting betting round for {next_stage}: {e}")
                 self.game.game_over = True; self.check_game_over(); return

             self.update_ui() # Show new community cards
             self.root.update() # Force draw

             # Start the betting process for this stage
             print(f"DEBUG GUI: Triggering process_next_turn for new stage: {next_stage}")
             self.root.after(500, self.process_next_turn)

         else:
              # Stage advancement failed or returned None (might mean round ended implicitly)
              print(f"Warning GUI: advance_to_next_stage returned {next_stage}. Checking round/game state.")
              if self.game and not self.game.round_over:
                  # If round isn't marked over, maybe force winner determination?
                   self.add_log_message("Warning: Stage advancement ended unexpectedly. Determining winner.")
                   self.root.after(100, self.determine_winner_and_proceed)
              else:
                  # Round is already over, just check game over status
                  self.check_game_over()


    def determine_winner_and_proceed(self):
        """Calls determine_winner_gui and then checks game over status."""
        print("DEBUG GUI: determine_winner_and_proceed called.")
        try:
            winner_info = self.game.determine_winner_gui()
            self.display_winner(winner_info)
        except AttributeError:
            messagebox.showerror("Game Error", "Game logic missing 'determine_winner_gui' method.")
            if self.game: self.game.game_over = True # Assume fatal
        except Exception as e:
            self.add_log_message(f"Error determining winner: {e}")
            import traceback; traceback.print_exc()
            # Decide if game should end on error determining winner
            # if self.game: self.game.game_over = True

        # ALWAYS check game over status after determining winner
        self.root.after(100, self.check_game_over)


    def display_winner(self, winner_info):
        """Displays winner information in the log."""
        if not winner_info: self.add_log_message("\nError: Winner info missing."); return

        winners = winner_info.get('winners', [])
        pot = winner_info.get('pot', 0) # Pot shown should be the pot *before* distribution
        details = winner_info.get('details', {})

        # --- Log Hand Results ---
        if details:
            self.add_log_message("--- Hand Results ---")
            # Get latest state AFTER pot distribution if possible (depends on when determine_winner runs)
            current_state = self.game.get_game_state_summary()
            player_states = current_state.get('players', {})

            # Try to display in original player order if possible, fallback to details keys
            player_order = list(self.game.players.keys()) if hasattr(self.game, 'players') else list(details.keys())
            displayed_players = set()

            for name in player_order:
                 if name in details:
                     detail = details.get(name)
                     player_state = player_states.get(name) # Get potentially updated state
                     if detail and player_state:
                          hole_cards = detail.get('hole_cards', player_state.get('cards', []))
                          hole_cards_str = " ".join(hole_cards) if hole_cards else "?? ??"
                          hand_type = detail.get('type', 'N/A')
                          best_5 = " ".join(detail.get('hand', [])) if detail.get('hand') else ""

                          log_line = f"  {name}: "
                          if player_state.get('folded'): log_line += f"Folded ({hole_cards_str})"
                          elif hand_type == 'Default (Others Folded)': log_line += f"Wins by default ({hole_cards_str})"
                          elif hand_type == 'Mucked/Invalid' or hand_type == 'Eval Error' or hand_type == 'Eval Exception':
                               log_line += f"{hand_type} ({hole_cards_str})"
                          elif hand_type != 'N/A': log_line += f"{hand_type} ({hole_cards_str} -> {best_5})"
                          else: log_line += f"Involved ({hole_cards_str})"
                          self.add_log_message(log_line)
                          displayed_players.add(name)

            # Display any remaining players from details not in original order (shouldn't happen often)
            for name in details:
                 if name not in displayed_players:
                    # Simplified display for players missed in order
                     player_state = player_states.get(name)
                     status = details[name].get('type', 'Unknown Status')
                     hole_cards_str = " ".join(details[name].get('hole_cards', [])) if details[name].get('hole_cards') else "??"
                     self.add_log_message(f"  {name}: ({hole_cards_str}) - {status}")


        # --- Log Winner Message ---
        distributed_pot = winner_info.get('distributed_pot', pot) # Use distributed amount if available
        if len(winners) == 1:
             winner = winners[0]
             win_msg = f"\n---> {winner} wins the pot of {distributed_pot}!"
             self.add_log_message(win_msg)
        elif len(winners) > 1:
             win_amount = winner_info.get('win_amount', 0) # Get amount per winner if provided
             win_msg = f"\n---> Split pot ({distributed_pot}) between: {', '.join(winners)}"
             if win_amount > 0: win_msg += f" ({win_amount} each)"
             self.add_log_message(win_msg)
        else: # No winners?
             if distributed_pot > 0: self.add_log_message(f"\n--- No winner declared for pot ({distributed_pot}). Check logic. ---")
             else: self.add_log_message("\n--- Round concludes. ---")

        # --- Log Heart Loss/Exchange (Based on Backend Logic/Flags) ---
        final_human_state = self.game.get_game_state_summary()['players'].get(self.player_name)
        if final_human_state:
             start_hearts = final_human_state.get('start_round_hearts')
             current_hearts = final_human_state.get('hearts')

             # Check for a flag indicating an exchange happened during check_game_over
             # (MatchManager would need to set this temporarily)
             # Example: if self.game.players[self.player_name].pop('_heart_exchanged_this_check', False):
             if getattr(self.game, '_human_exchanged_heart_flag', False):
                 self.add_log_message(f"---> {self.player_name} exchanged a heart for chips! ({current_hearts} left) <---")
                 self.game._human_exchanged_heart_flag = False # Reset flag

             # Log heart loss only if it happened *without* an exchange this cycle
             elif start_hearts is not None and current_hearts < start_hearts :
                  self.add_log_message(f"---> {self.player_name} lost a heart! ({current_hearts} left) <---")


        # Update UI one last time to show final chip/heart counts
        self.update_ui(show_bot_cards=True)
        self.root.update()


    def prepare_for_next_round_or_end(self):
        """Adds 'Next Round' button if game is not over."""
        print("DEBUG GUI: prepare_for_next_round_or_end called.")
        # Add check for game object existence
        if not self.game:
             print("DEBUG GUI: prepare... -> game object is None.")
             return
        if self.game.game_over:
             print("DEBUG GUI: prepare... -> game is over. No button.")
             return

        # Clean up previous button
        if hasattr(self, 'next_round_button') and self.next_round_button:
            try:
                if self.next_round_button.winfo_exists():
                     self.next_round_button.destroy()
                # Use delattr for safety if unsure if button exists
                if hasattr(self, 'next_round_button'): delattr(self, 'next_round_button')
            except (tk.TclError, AttributeError, NameError): pass # Ignore errors if already gone

        # Add the button if game isn't over
        self.next_round_button = ttk.Button(self.game_frame, text="Start Next Round", command=self.click_next_round)
        # Place it below pot info, ensure it doesn't overlap exit button
        self.next_round_button.grid(row=1, column=1, pady=10, sticky="s", columnspan=1) # Use grid row 1 again
        print("DEBUG GUI: prepare... -> Added Next Round button.")

    def click_next_round(self):
        """Starts the next round when the button is clicked."""
        print("DEBUG GUI: click_next_round called.")
        if hasattr(self, 'next_round_button') and self.next_round_button:
            try:
                 if self.next_round_button.winfo_exists():
                      self.next_round_button.destroy()
                 if hasattr(self, 'next_round_button'): delattr(self, 'next_round_button')
            except (tk.TclError, AttributeError, NameError): pass

        if self.game and not self.game.game_over:
            # Reset round-specific UI elements (backend handles game state reset)
            for lbl in self.community_card_labels:
                 if self.card_back_image: lbl.config(image=self.card_back_image); lbl.image = self.card_back_image
                 else: lbl.config(image=''); lbl.image = None
            self.current_round_name = "" # Reset stage name display
            self.start_new_round() # Tell backend to start the new round
        elif self.game and self.game.game_over:
             messagebox.showinfo("Game Over", "The game has already ended.")
        else:
             messagebox.showerror("Error", "Game logic is missing.")


    def check_game_over(self):
        """Checks game over status from MatchManager and handles the outcome."""
        print("DEBUG GUI: check_game_over called.")
        if not self.game: return

        # Ensure UI reflects the absolute latest state
        try:
            self.update_ui(show_bot_cards=True)
            self.root.update_idletasks()
        except tk.TclError: pass # Window might be closing

        # Check game over status using the backend method
        try:
            is_over, message, reason = self.game.check_game_over_status()
            print(f"DEBUG GUI: game.check_game_over_status() -> is_over={is_over}, reason={reason}, message={message}")
        except AttributeError:
             messagebox.showerror("Game Error", "Game logic missing 'check_game_over_status' method.")
             is_over, message, reason = True, "Game logic error", "internal" # Assume game over
             if self.game: self.game.game_over = True # Force flag
             if self.game and not hasattr(self.game, 'game_over_handled'): self.game.game_over_handled = False
        except Exception as e:
             messagebox.showerror("Game Error", f"Error checking game over status: {e}")
             is_over, message, reason = True, "Game logic error", "internal"
             if self.game: self.game.game_over = True
             if self.game and not hasattr(self.game, 'game_over_handled'): self.game.game_over_handled = False


        # Process game over only once using game_over_handled flag
        if is_over and not getattr(self.game, 'game_over_handled', False):
            if self.game:
                 self.game.game_over = True # Ensure main flag is set
                 self.game.game_over_handled = True # Prevent re-triggering
            self.disable_all_buttons()

            # Ensure 'Next Round' button is gone
            if hasattr(self, 'next_round_button') and self.next_round_button:
                 try:
                      if self.next_round_button.winfo_exists():
                           self.next_round_button.destroy()
                      if hasattr(self, 'next_round_button'): delattr(self, 'next_round_button')
                 except (tk.TclError, AttributeError, NameError): pass

            log_message = message or "The game has ended."
            self.add_log_message(f"\n--- {log_message} ---")

            # --- Adjusted Game Over Message/Sequence Trigger ---
            if reason == "hearts" or reason == "busted": # Human lost specifically
                self.add_log_message("--- Your deal with the Devil is done... ---")
                self.root.after(1500, self.show_game_over_sequence)
            elif reason == "bot_bust" or reason == "chips": # Player won due to bot bust or being last with chips
                 messagebox.showinfo("Game Over - You Win!", log_message)
                 self.add_log_message("--- YOU WIN! ---")
            else: # Other reasons (no_chips, internal error etc.)
                messagebox.showinfo("Game Over", log_message)
                self.add_log_message("--- GAME OVER ---")


        elif not is_over and getattr(self.game, 'round_over', False):
             # Round ended, game continues -> Show next round button
             print("DEBUG GUI: check_game_over -> Round over, game continues. Preparing next round button.")
             self.prepare_for_next_round_or_end()
        elif not is_over and not getattr(self.game, 'round_over', False):
            # Game/round still in progress
            print("DEBUG GUI: check_game_over -> Game/Round continue.")
        # else: game is over and already handled


    def show_game_over_sequence(self):
        """Displays the ending script when hearts run out."""
        if self.ending_frame: return # Already showing

        self.game_frame.pack_forget()
        self.log_frame.pack_forget()

        self.ending_frame = tk.Frame(self.root, bg="black")
        self.ending_frame.pack(fill=tk.BOTH, expand=True)

        self.ending_text_widget = Text(self.ending_frame, bg="black", fg="white", wrap=tk.WORD,
                                       padx=50, pady=50, bd=0, highlightthickness=0,
                                       font=self.SEQ_FONT_NORMAL)
        self.ending_text_widget.pack(fill=tk.BOTH, expand=True)
        self.ending_text_widget.config(state=tk.DISABLED)

        # Configure tags for text formatting
        self.ending_text_widget.tag_configure("devil", foreground=self.SEQ_COLOR_DEVIL, font=self.SEQ_FONT_DEVIL)
        self.ending_text_widget.tag_configure("narrator", foreground=self.SEQ_COLOR_NARRATOR, font=self.SEQ_FONT_NORMAL)
        self.ending_text_widget.tag_configure("man", foreground=self.SEQ_COLOR_MAN, font=self.SEQ_FONT_NORMAL)
        self.ending_text_widget.tag_configure("center", justify='center')
        self.ending_text_widget.tag_configure("prompt", foreground=self.SEQ_COLOR_DEFAULT, font=self.SEQ_FONT_NORMAL, justify='center')

        # --- Game Over Script ---
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
            ("戒賭熱線1834633(按2字)", "prompt", -1),
            ("", None, 1000),
            ("\n\n(Press any key or click to close the table)", "prompt", 0)
        ]

        self.ending_current_line = 0
        self._display_next_ending_line() # Start showing lines

        # Bind key/click to exit
        self.root.bind("<KeyPress>", self._end_game_sequence_key)
        self.ending_frame.bind("<Button-1>", self._end_game_sequence_key)
        self.ending_text_widget.bind("<Button-1>", self._end_game_sequence_key)


    def _display_next_ending_line(self):
        """Internal method to display script lines sequentially."""
        if not self.ending_text_widget or not self.ending_frame: return

        if self.ending_current_line >= len(self.ending_script_lines): return # Done

        line, tag, delay_ms = self.ending_script_lines[self.ending_current_line]

        try:
            self.ending_text_widget.config(state=tk.NORMAL)
            if tag: self.ending_text_widget.insert(tk.END, line + "\n", tag)
            else: self.ending_text_widget.insert(tk.END, line + "\n")
            self.ending_text_widget.see(tk.END)
            self.ending_text_widget.config(state=tk.DISABLED)
        except tk.TclError: print("Error: Ending text widget likely destroyed."); return

        self.ending_current_line += 1

        # Schedule next line if applicable
        if delay_ms > 0 and self.ending_current_line < len(self.ending_script_lines):
            if self.ending_after_id:
                 try: self.root.after_cancel(self.ending_after_id)
                 except ValueError: pass # Ignore if already cancelled
            self.ending_after_id = self.root.after(delay_ms, self._display_next_ending_line)
        elif self.ending_current_line >= len(self.ending_script_lines):
             # Ensure last line (prompt) is fully visible
             try: self.ending_text_widget.see(tk.END)
             except tk.TclError: pass


    def _end_game_sequence_key(self, event=None):
        """Handles key press or click during the ending sequence to quit."""
        if self.ending_after_id:
            try: self.root.after_cancel(self.ending_after_id); self.ending_after_id = None
            except ValueError: pass

        # Unbind events
        try:
            self.root.unbind("<KeyPress>")
            if self.ending_frame and self.ending_frame.winfo_exists():
                 self.ending_frame.unbind("<Button-1>")
            if self.ending_text_widget and self.ending_text_widget.winfo_exists():
                 self.ending_text_widget.unbind("<Button-1>")
        except tk.TclError: pass

        # Quit application
        self._quit_game(force=True) # Force quit without confirmation now


    def _confirm_quit(self):
        """Handles quit request from window close or Exit button."""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit the game?"):
            self._quit_game(force=True)

    def _quit_game(self, force=False):
        """Performs cleanup and quits the application."""
        if not force:
             if not messagebox.askokcancel("Quit", "Are you sure you want to quit the game?"):
                 return

        self.add_log_message("--- Game exited by player ---")
        try:
            # Cancel any pending 'after' jobs
            widget = self.root
            after_ids = widget.tk.call('after', 'info')
            for after_id in after_ids:
                try:
                     widget.after_cancel(after_id)
                except tk.TclError:
                     pass # Ignore if already cancelled/invalid

            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass


# --- Main Execution ---
if __name__ == "__main__":
    main_root = tk.Tk()
    app = PokerGUI(main_root)
    main_root.mainloop()