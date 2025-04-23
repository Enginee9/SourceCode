import random
import traceback
from Deck import Deck
from HandEvaluator import HandEvaluator, HandRank # Import HandRank if needed for comparisons/logging
from BotPlayer import BotPlayer
# Make sure these files exist and contain the necessary classes
# Define constants
INITIAL_HEARTS = 5 # Default starting hearts, can be overridden
HEART_CHIP_EXCHANGE_AMOUNT = 1000 # Amount of chips received for 1 heart

class PokerGame:
    """Manages the poker game logic for the GUI."""

    def __init__(self, player_name, bot_count, bot_difficulty, initial_hearts, initial_chips=1000):
        print(f"DEBUG MM: Initializing PokerGame - P:{player_name}, B:{bot_count}, D:{bot_difficulty}, H:{initial_hearts}, C:{initial_chips}")
        self.initial_chips = initial_chips
        self.players = {}
        self.bots = []
        self.human_player_name = player_name
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.previous_bet = 0 # Tracks the bet level *before* the current_bet (for min raise calc)
        self.last_raiser = None # Tracks the name of the last player who raised/bet
        self.current_stage = None # 'pre-flop', 'flop', 'turn', 'river', 'showdown'
        self.round_over = False
        self.game_over = False
        self.game_over_handled = False # Flag to prevent multiple game over triggers
        self._game_over_reason = "" # Stores reason like 'busted', 'hearts', 'chips'
        self.small_blind = max(1, initial_chips // 100) # Example calculation
        self.big_blind = max(1, initial_chips // 50) # Example calculation
        # Ensure BB is at least 2*SB
        if self.big_blind < self.small_blind * 2:
            self.big_blind = self.small_blind * 2
        print(f"DEBUG MM: Blinds calculated - SB: {self.small_blind}, BB: {self.big_blind}")

        self.turn_order_this_round = [] # List of player names in order of action for the current betting round
        self.current_player_turn_index = -1 # Index into turn_order_this_round
        self._human_exchanged_heart_flag = False # Internal flag for GUI logging of heart exchange
        self._player_action_count_this_betting_round = {} # Track actions per player in betting round
        self._aggressor_acted_this_cycle = False # Track if last raiser acted since raising (not strictly necessary with action count but can be useful)

        # Add Human Player
        self.players[player_name] = {
            'chips': self.initial_chips,
            'hearts': initial_hearts,
            'cards': [],
            'current_round_bet': 0,       # Bet amount in this specific betting round (pre-flop, flop, etc.)
            'total_round_investment': 0,  # Total chips put in the pot THIS ENTIRE HAND (sum across all betting rounds) - needed for side pots
            'folded': False,
            'all_in': False,
            'is_bot': False,
            'start_round_chips': self.initial_chips, # Chips at the absolute start of the hand
            'start_round_hearts': initial_hearts     # Hearts at the absolute start of the hand
        }
        print(f"DEBUG MM: Added player {player_name} with {self.initial_chips} chips and {initial_hearts} hearts.")

        # Add Bots
        for i in range(bot_count):
            bot_name = f"Bot_{i+1}"
            try:
                bot_player = BotPlayer(bot_name, self.initial_chips, initial_hearts)
                bot_player.difficulty = bot_difficulty
                self.bots.append(bot_player)
                self.players[bot_name] = {
                    'chips': self.initial_chips,
                    'hearts': initial_hearts, # Bots technically don't use hearts, but store for consistency
                    'cards': [],
                    'current_round_bet': 0,
                    'total_round_investment': 0,
                    'folded': False,
                    'all_in': False,
                    'is_bot': True,
                    'bot_instance': bot_player, # Reference to the BotPlayer object
                    'start_round_chips': self.initial_chips,
                    'start_round_hearts': initial_hearts
                }
                print(f"DEBUG MM: Added bot {bot_name} with {self.initial_chips} chips and {initial_hearts} hearts.")
            except Exception as e:
                print(f"ERROR MM: Failed to create/add bot {bot_name}: {e}")
                traceback.print_exc()

        # Initialize Dealer Button
        player_names = list(self.players.keys())
        if player_names:
            self.dealer_button_index = random.randrange(len(player_names))
            self.dealer_button_player = player_names[self.dealer_button_index]
            print(f"DEBUG MM: Initial dealer button set to {self.dealer_button_player}")
        else:
            self.dealer_button_index = -1
            self.dealer_button_player = None
            print("WARNING MM: No players found to assign dealer button.")

        # Initialize Hand Evaluator
        try:
            self.hand_evaluator = HandEvaluator()
        except Exception as e:
            print(f"FATAL ERROR: Failed to initialize HandEvaluator: {e}")
            raise

        print(f"DEBUG MM: PokerGame initialization complete.")


    def get_game_state_summary(self):
        """Returns a dictionary summarizing the current game state for the GUI."""
        players_summary = {}
        for name, p_state in self.players.items():
            # Provide default values for safety if a key is missing
            players_summary[name] = {
                'chips': p_state.get('chips', 0),
                'hearts': p_state.get('hearts', 0),
                'cards': list(p_state.get('cards', [])), # Return a copy
                'current_round_bet': p_state.get('current_round_bet', 0),
                'folded': p_state.get('folded', False),
                'all_in': p_state.get('all_in', False),
                'is_bot': p_state.get('is_bot', False),
                # Include start of round values for potential UI display/comparison
                 'start_round_chips': p_state.get('start_round_chips'),
                 'start_round_hearts': p_state.get('start_round_hearts')
            }

        current_turn_player = None
        # Determine current player only if round/game not over and turn order exists
        if not self.round_over and not self.game_over and self.turn_order_this_round and 0 <= self.current_player_turn_index < len(self.turn_order_this_round):
             current_turn_player = self.turn_order_this_round[self.current_player_turn_index]
             # Sanity check: Log if the supposed current player is actually ineligible
             player_state = self.players.get(current_turn_player)
             if player_state and (player_state.get('folded') or player_state.get('all_in')):
                  print(f"WARN MM Summary: Reporting turn={current_turn_player}, but player state is folded/all_in. Index might be wrong.")

        return {
            'players': players_summary,
            'community_cards': list(self.community_cards), # Return a copy
            'pot': self.pot,
            'current_bet': self.current_bet,
            'previous_bet': self.previous_bet, # Add previous bet level
            'current_stage': self.current_stage,
            'dealer_button_player': self.dealer_button_player,
            'current_turn_player': current_turn_player, # Name of player whose turn it is
            'small_blind': self.small_blind, # Pass blind info
            'big_blind': self.big_blind,
        }

    def start_new_round_get_info(self):
        """Resets round, deals, posts blinds, determines turn order."""
        print("\nDEBUG MM: --- Starting New Round ---")
        if self.game_over:
            print("DEBUG MM: StartNewRound called but game is already over.")
            return {'error': 'Game is already over.', 'game_over': True}

        # --- Check for Game Over Conditions BEFORE starting ---
        # Check Human player FIRST to allow heart exchange before checking bots/chip counts
        is_over_pre_round, _, reason_pre_round = self.check_game_over_status()
        if is_over_pre_round:
             print(f"DEBUG MM: StartNewRound detected game over immediately (Reason: {reason_pre_round}).")
             # Ensure game over flags are fully set if check_game_over_status didn't handle it (e.g., race condition)
             if not self.game_over: self.game_over = True
             if not self.game_over_handled: self.game_over_handled = True
             # Use message from check_game_over if available
             msg = f"Game is over ({reason_pre_round}). Cannot start new round."
             if reason_pre_round == 'busted': msg = f"{self.human_player_name} has no chips and no hearts left!"
             elif reason_pre_round == 'hearts': msg = f"{self.human_player_name}, you have lost all your hearts!"
             return {'error': msg, 'game_over': True}

        # Bot bust check (simplified: check if any bot has 0 chips AFTER potential human exchange)
        bot_names = [b.name for b in self.bots]
        busted_bot_name = None
        for bot_name in bot_names:
            if bot_name in self.players and self.players[bot_name].get('chips', 0) <= 0:
                busted_bot_name = bot_name
                print(f"DEBUG MM: StartNewRound - Bot '{busted_bot_name}' has busted.")
                break # Found a busted bot
        if busted_bot_name:
             self.game_over = True; self._game_over_reason = 'bot_bust'
             final_message = f"{self.human_player_name} wins! Bot {busted_bot_name} is out of chips."
             return {'error': final_message, 'game_over': True}

        # Filter active players (those with chips > 0) AGAIN after potential exchange
        active_players_with_chips = [name for name, p in self.players.items() if p.get('chips', 0) > 0]
        if len(active_players_with_chips) <= 1:
             winner_name = active_players_with_chips[0] if active_players_with_chips else "No one"
             print(f"DEBUG MM: StartNewRound - Only {winner_name} has chips.")
             self.game_over = True; self._game_over_reason = 'chips'
             final_message = f"{winner_name} wins! All other players are out of chips." if active_players_with_chips else "Game over! No players have chips."
             return {'error': final_message, 'game_over': True}
        # --- End Pre-Round Game Over Checks ---

        # --- Reset Round States ---
        self.deck.reset_and_shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.previous_bet = 0 # Reset previous bet level
        self.last_raiser = None
        self.round_over = False
        self.current_stage = 'pre-flop'
        self._human_exchanged_heart_flag = False # Reset the exchange flag HERE
        self._player_action_count_this_betting_round = {} # Reset action counts
        self._aggressor_acted_this_cycle = False

        # Reset player states for the new round
        for name, player_state in self.players.items():
             self._player_action_count_this_betting_round[name] = 0
             if name in active_players_with_chips:
                 # Store starting chips AND hearts for the round
                 player_state.update({
                     'cards': [],
                     'current_round_bet': 0,
                     'total_round_investment': 0,
                     'folded': False,
                     'all_in': False,
                     'start_round_chips': player_state['chips'], # Store chips at start of this hand
                     'start_round_hearts': player_state['hearts'] # Store hearts at start of this hand
                 })
             else:
                 # Mark inactive players as folded
                 player_state.update({'folded': True, 'all_in': False})
                 # Store starting values even if inactive (for consistency)
                 player_state['start_round_chips'] = player_state['chips']
                 player_state['start_round_hearts'] = player_state['hearts']
        # --- End Reset Round States ---

        # --- Move Dealer Button ---
        # Find the index of the current dealer among the *active* players
        current_dealer_idx_in_active = -1
        if self.dealer_button_player in active_players_with_chips:
             current_dealer_idx_in_active = active_players_with_chips.index(self.dealer_button_player)
        else:
            # If current dealer is inactive, find the next active player clockwise
            original_player_list = list(self.players.keys())
            try:
                 search_start_idx = original_player_list.index(self.dealer_button_player) if self.dealer_button_player else -1
                 if search_start_idx != -1:
                     for i in range(1, len(original_player_list) + 1):
                         next_idx = (search_start_idx + i) % len(original_player_list)
                         next_player = original_player_list[next_idx]
                         if next_player in active_players_with_chips:
                             # Find the index of this *next* player in the active list, then go back one to find the effective previous dealer's index
                             effective_last_dealer_idx = active_players_with_chips.index(next_player) - 1
                             current_dealer_idx_in_active = effective_last_dealer_idx % len(active_players_with_chips)
                             break
            except (ValueError, IndexError) as e:
                 print(f"Warning MM: Error finding previous dealer '{self.dealer_button_player}': {e}")
                 current_dealer_idx_in_active = -1 # Fallback

        # If still not found (or first round), assign randomly relative to active players
        if current_dealer_idx_in_active == -1:
            current_dealer_idx_in_active = random.randrange(len(active_players_with_chips)) - 1
            current_dealer_idx_in_active = max(-1, current_dealer_idx_in_active) % len(active_players_with_chips)

        # Move to the next active player
        new_dealer_idx_in_active = (current_dealer_idx_in_active + 1) % len(active_players_with_chips)
        self.dealer_button_player = active_players_with_chips[new_dealer_idx_in_active]
        # Update the main index (though less critical now)
        self.dealer_button_index = list(self.players.keys()).index(self.dealer_button_player)
        print(f"DEBUG MM: Dealer button moved to {self.dealer_button_player}")
        # --- End Move Dealer Button ---

        # --- Determine Blinds Positions (Relative to Active Players) ---
        num_active = len(active_players_with_chips)
        # Default SB/BB positions
        sb_idx = (new_dealer_idx_in_active + 1) % num_active
        bb_idx = (new_dealer_idx_in_active + 2) % num_active
        # Heads-up case: Dealer is SB, other player is BB
        if num_active == 2:
            sb_idx = new_dealer_idx_in_active
            bb_idx = (new_dealer_idx_in_active + 1) % num_active
        # Find the actual player names
        sb_player = active_players_with_chips[sb_idx]
        bb_player = active_players_with_chips[bb_idx]

        # --- Post Blinds ---
        sb_amount = self._post_bet(sb_player, self.small_blind)
        print(f"DEBUG MM: {sb_player} posts SB {sb_amount}.")
        bb_amount = self._post_bet(bb_player, self.big_blind)
        print(f"DEBUG MM: {bb_player} posts BB {bb_amount}.")
        self.current_bet = self.big_blind # Initial bet level is the BB
        self.previous_bet = 0 # No previous bet before the BB
        # --- End Post Blinds ---

        # --- Deal Hole Cards ---
        try:
            num_cards_to_deal = 2
            for _ in range(num_cards_to_deal):
                # Deal one card at a time, starting left of dealer
                deal_start_offset = (new_dealer_idx_in_active + 1) % num_active
                for i in range(num_active):
                    player_to_deal_idx = (deal_start_offset + i) % num_active
                    player_name = active_players_with_chips[player_to_deal_idx]
                    card = self.deck.deal_card()
                    if not card:
                        raise ValueError("Deck ran out of cards during initial deal!")
                    self.players[player_name]['cards'].append(card)
            print("DEBUG MM: Hole cards dealt.")
            # Optional: Log player's hand for debug
            # print(f"DEBUG MM: Player {self.human_player_name} cards: {self.players[self.human_player_name]['cards']}")
        except ValueError as e:
             print(f"ERROR MM: {e}")
             # Handle deck running out - should not happen with standard deck/players
             self.game_over = True; self._game_over_reason = 'deck_error'
             return {'error': f'{e} This should not happen.', 'game_over': True}
        # --- End Deal Hole Cards ---

        # --- Determine Pre-flop Turn Order ---
        # Action starts left of the Big Blind
        first_act_idx = (bb_idx + 1) % num_active
        # Heads-up Exception: SB (dealer) acts first pre-flop
        if num_active == 2:
             first_act_idx = sb_idx

        # Create the ordered list for this round
        self.turn_order_this_round = active_players_with_chips[first_act_idx:] + active_players_with_chips[:first_act_idx]
        self.last_raiser = bb_player # BB is the initial "raiser" pre-flop

        # Find the first player in the order who can actually act (not all-in already from blinds)
        self.current_player_turn_index = -1
        for i, name in enumerate(self.turn_order_this_round):
             if not self.players[name].get('all_in'):
                 self.current_player_turn_index = i
                 break
        # If loop completes and no one found (e.g., everyone all-in posting blinds), index remains -1 (or set to 0?)
        if self.current_player_turn_index == -1 and self.turn_order_this_round:
             print("Warning MM: Pre-flop - all players in turn order are all-in. Setting index to 0.")
             # This likely means the hand goes straight to dealing community cards if >1 player all-in
             self.current_player_turn_index = 0 # Point to the first player anyway
             # Or should the round end / betting be skipped? The is_betting_over check should handle this.

        print(f"DEBUG MM: Pre-flop turn order: {self.turn_order_this_round}")
        if self.turn_order_this_round and self.current_player_turn_index != -1:
            print(f"DEBUG MM: Starting turn index: {self.current_player_turn_index} ({self.turn_order_this_round[self.current_player_turn_index]})")
        else:
            print("DEBUG MM: No valid starting turn player found or all are all-in.")
        # --- End Pre-flop Turn Order ---

        # Log player's starting hearts again for clarity at round start
        human_start_hearts = self.players[self.human_player_name]['start_round_hearts']
        print(f"DEBUG MM: Player {self.human_player_name} starting round with {human_start_hearts} hearts (verified).")

        return {
            'turn_order': list(self.turn_order_this_round), # Send copy
            'start_index': self.current_player_turn_index,
            'dealer': self.dealer_button_player,
            'sb_player': sb_player,
            'sb_amount': sb_amount,
            'bb_player': bb_player,
            'bb_amount': bb_amount
        }

    def _post_bet(self, player_name, amount):
        """Helper to post a bet/blind, update player state, and handle all-in."""
        player = self.players[player_name]
        # Amount posted cannot exceed player's chips
        actual_amount = min(amount, player['chips'])

        if actual_amount <= 0:
             print(f"DEBUG MM: _post_bet called for {player_name} with amount {amount}, but chips are {player['chips']}. Posting 0.")
             return 0 # Cannot post negative or zero bet

        player['chips'] -= actual_amount
        player['current_round_bet'] += actual_amount
        player['total_round_investment'] += actual_amount # Track total investment in the hand
        self.pot += actual_amount

        # Check if player is now all-in
        if player['chips'] <= 0:
            player['all_in'] = True
            print(f"DEBUG MM:_post_bet {player_name} is All In for {actual_amount} (Total bet this round: {player['current_round_bet']})")
        # else: print(f"DEBUG MM: {player_name} posted {actual_amount}. Chips left: {player['chips']}.") # Verbose log

        return actual_amount

    def _advance_turn_index(self):
        """Finds the NEXT player in turn_order who can act (not folded, not all-in).
           Returns the new index or -1 if no one can act."""
        if not self.turn_order_this_round:
            print("Warning MM: _advance_turn_index called with empty turn order.")
            self.current_player_turn_index = -1
            return -1

        num_players_in_order = len(self.turn_order_this_round)
        if num_players_in_order == 0:
             self.current_player_turn_index = -1
             return -1

        # Get the index we are starting *from*
        original_index = self.current_player_turn_index
        # Handle invalid starting index (e.g., first call)
        if original_index < 0 or original_index >= num_players_in_order:
            original_index = -1 # Treat as if starting before the first player

        # Loop through players starting from the *next* position
        for i in range(1, num_players_in_order + 1):
            next_index = (original_index + i) % num_players_in_order
            next_player_name = self.turn_order_this_round[next_index]
            player_state = self.players.get(next_player_name)

            # Check if this player is eligible to act
            if player_state and not player_state.get('folded') and not player_state.get('all_in'):
                # Found the next player who can act
                self.current_player_turn_index = next_index
                print(f"DEBUG MM: Advanced turn index from {original_index} to {next_index} ({next_player_name})")
                return self.current_player_turn_index

        # If we loop through everyone and find no one eligible
        print("Warning MM: _advance_turn_index looped - no eligible player found to act.")
        self.current_player_turn_index = -1 # Indicate no one can act
        return -1

    def process_player_action(self, player_name, action, amount=0):
        """Processes a player's action (fold, check, call, raise, all in) and updates game state.
           'amount' for raise is the TOTAL bet amount the player wants to make.
           'amount' for other actions is ignored (calculated internally).
           Handles backend validation."""
        print(f"DEBUG MM: Received action: {player_name}, {action}, Amount Arg:{amount}")

        # --- Pre-Action Validation ---
        if self.round_over or self.game_over:
            print(f"Warning MM: Action received for {player_name} but round/game is over.")
            return # Ignore action

        # Verify it's actually this player's turn according to internal state
        current_player_expected = None
        if self.turn_order_this_round and 0 <= self.current_player_turn_index < len(self.turn_order_this_round):
            current_player_expected = self.turn_order_this_round[self.current_player_turn_index]

        if current_player_expected != player_name:
             print(f"ERROR MM: process_player_action called for {player_name} but internal index points to {current_player_expected}. State mismatch!")
             # Don't process the action, let the GUI resync or handle the error
             # Might need to call _advance_turn_index if stuck? Risky.
             return

        player = self.players.get(player_name)
        # Verify player exists and is eligible to act
        if not player:
             print(f"ERROR MM: Player {player_name} not found in game state.")
             self._advance_turn_index(); return # Skip turn if player missing
        if player['folded']:
            print(f"Warning MM: process_player_action called for folded player {player_name}. Advancing.")
            self._advance_turn_index(); return # Skip turn
        if player['all_in']:
             print(f"Warning MM: process_player_action called for all-in player {player_name}. Advancing.")
             self._advance_turn_index(); return # Skip turn
        # --- End Pre-Action Validation ---

        amount_to_call = max(0, self.current_bet - player['current_round_bet'])
        player_chips = player['chips']

        # Increment action count for this player in this betting round
        self._player_action_count_this_betting_round[player_name] = self._player_action_count_this_betting_round.get(player_name, 0) + 1
        # If this player was the last aggressor, mark that they have now acted
        if player_name == self.last_raiser:
            self._aggressor_acted_this_cycle = True # Useful for BB option check maybe

        # --- Process Specific Action ---
        try:
            processed = False # Flag to track if action was handled

            if action == "fold":
                player['folded'] = True
                print(f"DEBUG MM: {player_name} folded.")
                processed = True
                # Check if round ends immediately due to fold
                self._check_round_end_condition() # This might set self.round_over

            elif action == "check":
                if amount_to_call > 0:
                    raise ValueError(f"{player_name} cannot check. Must call {amount_to_call} or raise/fold.")
                print(f"DEBUG MM: {player_name} checked.")
                processed = True

            elif action == "call":
                if amount_to_call <= 0:
                    print(f"Warning MM: {player_name} called when check was possible. Treating as check.")
                    # Allow it, but log warning. No chips change.
                    processed = True
                else:
                    call_cost = min(amount_to_call, player_chips) # Can only call what they have
                    print(f"DEBUG MM: {player_name} attempting call. Cost: {call_cost}, ToCall: {amount_to_call}, Chips: {player_chips}")
                    if call_cost > 0:
                         self._post_bet(player_name, call_cost)
                         # Check if call resulted in all-in
                         if player['all_in']: action = "all in" # Update action if call made them all-in
                    else:
                         print(f"Warning MM: {player_name} called but call_cost is 0? Should have checked.")
                         # Allow check equivalent
                    print(f"DEBUG MM: {player_name} effectively called {call_cost}.")
                    processed = True


            elif action == "raise":
                 # 'amount' is the TOTAL desired bet level for the round
                 target_total_bet = amount
                 chips_needed_for_this_action = target_total_bet - player['current_round_bet']

                 # Basic validation: Raise must increase the bet, need chips
                 if chips_needed_for_this_action <= 0:
                      raise ValueError("Raise amount must be greater than current bet this round.")
                 if chips_needed_for_this_action > player_chips:
                      raise ValueError(f"Insufficient chips ({player_chips}) for raise cost ({chips_needed_for_this_action}). Target: {target_total_bet}")

                 # Min Raise Validation:
                 # Raise must be at least the size of the previous bet/raise in this round.
                 # Minimum increment is usually the Big Blind.
                 min_raise_increment = max(self.big_blind, self.current_bet - self.previous_bet)
                 # The minimum *total* bet a player must make if they raise.
                 min_legal_total_bet = self.current_bet + min_raise_increment

                 # Exception: An all-in raise doesn't *have* to meet the min increment if player lacks chips,
                 # but it still constitutes a raise if it's more than a call.
                 is_all_in_raise = (chips_needed_for_this_action == player_chips)

                 if not is_all_in_raise and target_total_bet < min_legal_total_bet:
                      raise ValueError(f"Raise target ({target_total_bet}) is less than minimum legal bet ({min_legal_total_bet}). Min increment: {min_raise_increment}")

                 # If validation passes, post the bet
                 print(f"DEBUG MM: {player_name} raising. Cost: {chips_needed_for_this_action}, Target Total: {target_total_bet}")
                 self._post_bet(player_name, chips_needed_for_this_action)

                 # Update game state for the raise
                 self.previous_bet = self.current_bet # The old high bet becomes the previous bet
                 self.current_bet = player['current_round_bet'] # The new high bet is this player's total round bet
                 self.last_raiser = player_name # This player is the new aggressor
                 print(f"DEBUG MM: Raise successful. New current_bet: {self.current_bet}, previous_bet: {self.previous_bet}")

                 # Reset action counts for everyone EXCEPT the raiser, whose count becomes 1
                 self._player_action_count_this_betting_round = {p_name: 0 for p_name in self.players}
                 self._player_action_count_this_betting_round[player_name] = 1
                 self._aggressor_acted_this_cycle = False # New betting cycle begins

                 processed = True


            elif action == "all in":
                all_in_cost = player_chips
                if all_in_cost <= 0:
                    # Should have been caught earlier, but safety check
                    print(f"Warning MM: {player_name} all-in with 0 chips? Advancing.")
                    player['all_in'] = True # Mark them just in case
                    processed = True # Treat as processed
                else:
                    print(f"DEBUG MM: {player_name} going All In for {all_in_cost}.")
                    self._post_bet(player_name, all_in_cost) # This will mark player['all_in'] = True
                    print(f"DEBUG MM: {player_name} total bet this round after All In: {player['current_round_bet']}")

                    # Check if the all-in constitutes a raise
                    if player['current_round_bet'] > self.current_bet:
                         print(f"DEBUG MM: All-in by {player_name} is a raise.")
                         # Is it a *legal* raise size (if not already all-in)?
                         min_raise_increment = max(self.big_blind, self.current_bet - self.previous_bet)
                         min_legal_total_bet = self.current_bet + min_raise_increment

                         # If the all-in amount meets or exceeds the min legal raise *total* bet
                         if player['current_round_bet'] >= min_legal_total_bet:
                             print(f"DEBUG MM: All-in meets minimum raise requirement.")
                             self.previous_bet = self.current_bet
                             self.current_bet = player['current_round_bet']
                             self.last_raiser = player_name
                             # Reset action counts
                             self._player_action_count_this_betting_round = {p_name: 0 for p_name in self.players}
                             self._player_action_count_this_betting_round[player_name] = 1
                             self._aggressor_acted_this_cycle = False
                         else:
                              # All-in is more than call, but less than a full min raise
                              # It doesn't *re-open* the betting fully, but players who haven't acted yet must call the new amount.
                              print(f"DEBUG MM: All-in is effective raise but under min raise size. Betting may not fully reopen.")
                              # Update current bet, but maybe DON'T reset action counts? Or handle specially in is_betting_over?
                              # Standard rules: It reopens betting if it's at least half a min raise? Complex.
                              # Simplified: Treat it as a raise for now, update bets, reset counts. Players might just call.
                              self.previous_bet = self.current_bet
                              self.current_bet = player['current_round_bet']
                              self.last_raiser = player_name # Still the aggressor
                              # Reset action counts - players need to call the new amount
                              self._player_action_count_this_betting_round = {p_name: 0 for p_name in self.players}
                              self._player_action_count_this_betting_round[player_name] = 1
                              self._aggressor_acted_this_cycle = False

                    # Else: All-in was just a call (or less than current bet if already partially in)
                    # No change needed to current_bet or last_raiser

                    processed = True

            else:
                print(f"Warning MM: Unknown action received: {action}")
                # Optionally raise error or just ignore and advance turn
                raise ValueError(f"Unknown action: {action}")

        except ValueError as e:
            # Handle validation errors (e.g., illegal check/raise)
            print(f"ERROR MM: Action processing error - {e}")
            # Re-raise the exception so the GUI can potentially catch it and inform user
            raise e

        finally:
            # Always advance turn index if the round didn't end, even if action failed validation (maybe?)
            # No, only advance if action was successfully processed or was fold/check/call(0).
            # If a raise failed validation, it should remain the player's turn.
            # Let's advance only if action was processed OR if round ended.
            if processed and not self.round_over:
                self._advance_turn_index()
            elif self.round_over:
                 print(f"DEBUG MM: Round ended after {player_name}'s action ({action}). Not advancing index.")
                 self.current_player_turn_index = -1 # Indicate no one's turn

    def _check_round_end_condition(self):
        """Checks if only one player remains active (not folded). If so, sets round_over."""
        if self.round_over: return # Already over

        not_folded_players = [name for name, p in self.players.items() if not p.get('folded')]
        if len(not_folded_players) <= 1:
             print(f"DEBUG MM: Round ending early, <=1 player not folded ({not_folded_players}).")
             self.round_over = True
             # Winner determined by default in determine_winner


    def is_betting_over(self):
        """Checks if the current betting round (e.g., flop) is complete."""
        # Condition 1: Round ended prematurely (e.g., only one player left)
        if self.round_over:
            print("DEBUG MM: is_betting_over: True (Round ended prematurely)")
            return True

        # Condition 2: Only one player eligible to bet (others folded or all-in)
        contesting_players = {name: p for name, p in self.players.items() if not p.get('folded')}
        if len(contesting_players) < 2:
            # If 0 or 1 player left who hasn't folded, betting is over.
            print(f"DEBUG MM: is_betting_over: True (<=1 player contesting: {list(contesting_players.keys())})")
            # Ensure round_over is set if betting ends this way
            if not self.round_over: self._check_round_end_condition() # Check again to set flag if needed
            return True

        # Condition 3: All remaining players are all-in
        eligible_actors = [name for name, p in contesting_players.items() if not p.get('all_in')]
        if not eligible_actors:
             # Everyone left in the hand is all-in
             print(f"DEBUG MM: is_betting_over: True (All {len(contesting_players)} contesting players are all-in)")
             # Community cards should be dealt out without further betting
             return True

        # Condition 4: Betting action has closed (everyone has acted and bets match)
        # Check if everyone still able to act has:
        #   a) Acted at least once since the last raise (or since the start if no raise).
        #   b) Matched the current highest bet (self.current_bet) or is all-in.

        all_bets_matched_or_all_in = True
        all_eligible_acted_this_cycle = True
        num_eligible_actors = 0 # Count players who *could* still act

        # Use the current turn order for checking action sequence
        if not self.turn_order_this_round:
             print("ERROR MM: is_betting_over called with empty turn_order! Assuming true.")
             return True # Cannot determine state, assume betting done

        for name in self.turn_order_this_round:
            player_state = self.players.get(name)
            # Only consider players still in the hand (not folded)
            if player_state and not player_state.get('folded'):
                # Focus on players who *can* still act (not all-in)
                if not player_state.get('all_in'):
                    num_eligible_actors += 1
                    # Check if their bet matches the current highest bet
                    if player_state['current_round_bet'] < self.current_bet:
                        all_bets_matched_or_all_in = False
                        # print(f"DEBUG MM is_betting_over: False ({name} bet {player_state['current_round_bet']} < current {self.current_bet})")
                        # break # Found someone who hasn't matched, no need to check further matching

                    # Check if they have acted in the current betting cycle
                    # Action count reset happens on a raise.
                    if self._player_action_count_this_betting_round.get(name, 0) < 1:
                         # Special case: Pre-flop BB option
                         is_preflop = self.current_stage == 'pre-flop'
                         is_bb = (name == self.last_raiser and self.current_bet == self.big_blind) # Check if it's the original BB

                         # Allow BB to act if no raise occurred and action gets back to them
                         if is_preflop and is_bb and self.current_bet == self.big_blind:
                              # If the bet is still just the BB, the BB gets an option to raise
                              # even if their action count is 0 (from posting blind).
                              # They only get this option once.
                              all_eligible_acted_this_cycle = True # Don't block completion for BB option yet
                              print(f"DEBUG MM is_betting_over: Allowing BB option check for {name}")
                         else:
                              # This player hasn't acted since the last raise/start of round
                              all_eligible_acted_this_cycle = False
                              # print(f"DEBUG MM is_betting_over: False ({name} hasn't acted this cycle - count {self._player_action_count_this_betting_round.get(name, 0)})")
                              break # Found someone yet to act, no need to check further actions
                # else: Player is folded or all-in, don't care about their bet match/action count

        # If we finished the loop, evaluate the conditions
        # Need to have completed a full circle AND bets need to match (or players all-in)
        # Also, ensure there was at least one eligible actor to begin with (handles cases where only all-ins remain)
        betting_is_complete = (num_eligible_actors > 0 and all_eligible_acted_this_cycle and all_bets_matched_or_all_in)

        # Handle the BB option explicitly
        is_preflop_bb_option_case = False
        if self.current_stage == 'pre-flop' and self.current_bet == self.big_blind:
             # Find the original BB player (who was the first 'last_raiser')
             # Need to store original BB? Or deduce from turn order / blind posting info?
             # Let's assume self.last_raiser holds the BB initially if no raise has happened.
             bb_player = self.last_raiser
             bb_state = self.players.get(bb_player)
             # Check if action is on BB and they haven't acted yet (count=0)
             if bb_state and not bb_state['all_in'] and not bb_state['folded'] and \
                self.turn_order_this_round and self.current_player_turn_index >= 0 and \
                self.turn_order_this_round[self.current_player_turn_index] == bb_player and \
                self._player_action_count_this_betting_round.get(bb_player, 0) == 0:
                 is_preflop_bb_option_case = True
                 betting_is_complete = False # BB still has option, betting not over
                 print(f"DEBUG MM: is_betting_over: False (Pre-flop BB {bb_player} has option)")


        if betting_is_complete:
             print(f"DEBUG MM: is_betting_over: True (All acted & matched at {self.current_bet})")
             return True
        elif not is_preflop_bb_option_case: # Avoid logging false negative if just waiting on BB
             # print(f"DEBUG MM: is_betting_over: False (Actors:{num_eligible_actors}, Acted Cycle:{all_eligible_acted_this_cycle}, Matched:{all_bets_matched_or_all_in})")
             pass # Reduce log noise

        return False # Default: betting continues


    def advance_to_next_stage(self):
        """Deals community cards or moves to Showdown. Returns the name of the new stage or None."""
        if self.round_over or self.game_over:
             print(f"DEBUG MM: Advance stage called but round/game over. Current stage: {self.current_stage}")
             return None

        # Check if betting is actually over for the current stage first
        if not self.is_betting_over():
             print(f"Warning MM: Tried to advance stage '{self.current_stage}' but betting is not over yet.")
             return None # Cannot advance yet

        print(f"DEBUG MM: Advancing stage from {self.current_stage}")

        next_stage_map = {'pre-flop': 'flop', 'flop': 'turn', 'turn': 'river', 'river': 'showdown'}
        card_deal_map = {'flop': 3, 'turn': 1, 'river': 1} # Cards to deal for each stage

        if self.current_stage in next_stage_map:
            next_stage = next_stage_map[self.current_stage]
            self.current_stage = next_stage # Update internal stage tracker

            if next_stage == 'showdown':
                self.round_over = True # Mark round as fully over
                print("DEBUG MM: Moving to Showdown.")
                return 'showdown'
            else:
                # --- Reset betting state for the NEW betting round ---
                # Handled by start_next_betting_round called by GUI/controller
                # self.current_bet = 0; self.previous_bet = 0; self.last_raiser = None
                # self._player_action_count_this_betting_round = {p: 0 for p in self.players}
                # self._aggressor_acted_this_cycle = False
                # --- End Reset ---

                num_cards_to_deal = card_deal_map.get(next_stage, 0)
                if num_cards_to_deal > 0:
                     try:
                         # Burn a card before dealing community cards
                         if len(self.deck) > 0: self.deck.burn_card()
                         else: raise ValueError("Deck empty before burning card!")

                         dealt_cards = []
                         for _ in range(num_cards_to_deal):
                             card = self.deck.deal_card()
                             if card:
                                 self.community_cards.append(card)
                                 dealt_cards.append(card)
                             else:
                                 # This should be rare unless deck setup is wrong
                                 raise ValueError(f"Deck empty while dealing {next_stage}!")
                         print(f"DEBUG MM: Dealt {next_stage.capitalize()}: {dealt_cards} -> Community: {self.community_cards}")
                         return next_stage # Return name of stage dealt ('flop', 'turn', 'river')
                     except ValueError as e:
                          print(f"ERROR MM: Failed to deal cards for {next_stage}: {e}")
                          self.game_over = True; self._game_over_reason = 'deck_error'
                          return None # Indicate error
                     except Exception as e: # Catch other potential deck errors
                          print(f"ERROR MM: Unexpected error during card dealing: {e}")
                          traceback.print_exc()
                          self.game_over = True; self._game_over_reason = 'internal_error'
                          return None
                else:
                     print(f"Warning MM: No cards defined to deal for stage {next_stage}")
                     return next_stage # Still return stage name?

        else:
            # Should not happen if logic is correct
            print(f"Warning MM: Cannot advance stage from unknown stage: {self.current_stage}")
            return None

    def start_next_betting_round(self):
        """Resets betting vars & determines turn order for Flop/Turn/River.
           Called by controller *after* advance_to_next_stage deals cards."""
        if self.round_over or self.game_over:
            print("Warning MM: start_next_betting_round called when round/game over.")
            return {'turn_order': [], 'start_index': -1}
        if self.current_stage == 'pre-flop' or self.current_stage == 'showdown':
             print(f"Warning MM: start_next_betting_round called at invalid stage: {self.current_stage}.")
             # Return current state if pre-flop, empty if showdown
             current_index = self.current_player_turn_index if self.current_stage == 'pre-flop' else -1
             current_order = list(self.turn_order_this_round) if self.current_stage == 'pre-flop' else []
             return {'turn_order': current_order, 'start_index': current_index}

        print(f"DEBUG MM: Starting next betting round for stage: {self.current_stage}")

        # Reset betting state for the new round
        self.current_bet = 0
        self.previous_bet = 0
        self.last_raiser = None
        self._player_action_count_this_betting_round = {p: 0 for p in self.players} # Reset action counts
        self._aggressor_acted_this_cycle = False # Reset flag

        # Reset current_round_bet for players still in the hand and not all-in
        contesting_players = [] # List of names still in the hand
        original_order = list(self.players.keys()) # Keep original order for reference
        for name in original_order:
            player_state = self.players[name]
            if not player_state.get('folded'):
                 contesting_players.append(name)
                 # Reset bet for the new street IF they are not already all-in
                 if not player_state.get('all_in'):
                     player_state['current_round_bet'] = 0
                 # else: Keep all-in player's bet as is (it's their total for the hand)

        if not contesting_players:
             print("Warning MM: No contesting players found for next betting round.")
             # This case should ideally be caught earlier by round end checks
             self.round_over = True
             return {'turn_order': [], 'start_index': -1}

        # Determine turn order for post-flop rounds: starts left of the dealer button
        # among players still in the hand (contesting_players).
        dealer_idx_original = -1
        if self.dealer_button_player in original_order:
            dealer_idx_original = original_order.index(self.dealer_button_player)

        first_actor_name = None
        # Find the first contesting player starting from dealer's left
        if dealer_idx_original != -1:
            for i in range(len(original_order)):
                 check_idx = (dealer_idx_original + 1 + i) % len(original_order)
                 check_name = original_order[check_idx]
                 if check_name in contesting_players:
                     first_actor_name = check_name
                     break

        # Fallback if dealer not found or no contesting player found clockwise (shouldn't happen)
        if not first_actor_name:
            print("Warning MM: Could not determine first actor post-flop based on dealer. Using first contesting player.")
            if contesting_players:
                first_actor_name = contesting_players[0]
            else:
                 # Should be impossible if we got here, but handle defensively
                 print("ERROR MM: No contesting players left to determine turn order.")
                 self.round_over = True
                 return {'turn_order': [], 'start_index': -1}

        # Create the turn order list starting with the first actor
        start_idx_in_contesting = contesting_players.index(first_actor_name)
        self.turn_order_this_round = contesting_players[start_idx_in_contesting:] + contesting_players[:start_idx_in_contesting]

        # Find the first player in the new order who is NOT all-in (can actually act)
        self.current_player_turn_index = -1
        for i, name in enumerate(self.turn_order_this_round):
             if not self.players[name].get('all_in'):
                 self.current_player_turn_index = i
                 break

        if self.current_player_turn_index == -1:
             # This means all remaining players are all-in post-flop. Betting is skipped.
             print(f"DEBUG MM: All remaining players ({len(self.turn_order_this_round)}) are all-in post-flop. No betting for {self.current_stage}.")
             # Keep the turn order for reference, but set index to -1 to signal no action
             self.turn_order_this_round = [] # Clear order to signify no action turns
             return {'turn_order': [], 'start_index': -1}

        # Betting round will proceed
        print(f"DEBUG MM: New turn order for {self.current_stage}: {self.turn_order_this_round}")
        print(f"DEBUG MM: Starting turn index: {self.current_player_turn_index} ({self.turn_order_this_round[self.current_player_turn_index]})")

        return {'turn_order': list(self.turn_order_this_round), 'start_index': self.current_player_turn_index}


    def determine_winner_gui(self):
        """Determines winner(s), awards pot(s), handles heart deduction. Returns dict with winner info."""
        print("DEBUG MM: Determining winner...")
        if not self.round_over:
            print("Warning MM: determine_winner called but round is not over.")
            self.round_over = True # Force round over state

        winner_info = {
            'winners': [],
            'pot': self.pot,
            'details': {},
            'win_amount': 0,
            'distributed_pot': 0
        }

        try:
            main_pot_amount = self.pot
            eligible_players = {name: p for name, p in self.players.items() if not p.get('folded')}
            eligible_names = list(eligible_players.keys())

            if len(eligible_players) == 0:
                print("Warning MM: No eligible players found at end of round. Pot disappears?")
                winner_info['distributed_pot'] = 0
            elif len(eligible_players) == 1:
                winner_name = eligible_names[0]
                winner_info['winners'] = [winner_name]
                winner_state = eligible_players[winner_name]
                winner_info['details'][winner_name] = {
                    'type': 'Default (Others Folded)',
                    'hand': [],
                    'hole_cards': winner_state.get('cards', [])
                }
                win_amount = main_pot_amount
                winner_info['win_amount'] = win_amount
                winner_info['distributed_pot'] = win_amount
                self.players[winner_name]['chips'] += win_amount
                print(f"DEBUG MM: {winner_name} wins {win_amount} by default.")
            else:
                # Showdown logic (remains the same)
                best_hands = {}
                evaluated_details = {}
                print(f"DEBUG MM: Showdown between: {eligible_names}")
                print(f"DEBUG MM: Community Cards: {self.community_cards}")
                for name, player_state in eligible_players.items():
                    hole_cards = player_state.get('cards', [])
                    if not hole_cards:
                        print(f"Warning MM: Player {name} in showdown has no hole cards?")
                        evaluated_details[name] = {'type': 'Missing Cards', 'hole_cards': []}
                        continue
                    try:
                        rank_obj, best_5_card_strings = self.hand_evaluator.evaluate_hand(
                            hole_cards, self.community_cards
                        )
                        if rank_obj is not None:
                            best_hands[name] = rank_obj
                            evaluated_details[name] = {
                                'type': rank_obj.rank_name,
                                'hand': best_5_card_strings,
                                'hole_cards': hole_cards
                            }
                            print(f"DEBUG MM Eval Result: {name} -> {rank_obj.rank_name} (Kickers: {rank_obj.kickers}), Hand: {best_5_card_strings}, Hole: {hole_cards}")
                        else:
                            print(f"ERROR MM: Hand evaluation returned None for {name}")
                            evaluated_details[name] = {'type': 'Eval Error (None)', 'hole_cards': hole_cards}
                    except Exception as e:
                        print(f"ERROR MM: Hand evaluation failed unexpectedly for {name}: {e}")
                        traceback.print_exc()
                        evaluated_details[name] = {'type': 'Eval Exception', 'hole_cards': hole_cards}

                winner_info['details'] = evaluated_details

                if best_hands:
                    winning_rank_obj = max(best_hands.values())
                    winners = [name for name, rank_obj in best_hands.items() if rank_obj == winning_rank_obj]
                    winner_info['winners'] = winners
                    if winners:
                        num_winners = len(winners)
                        win_amount_each = main_pot_amount // num_winners
                        remainder = main_pot_amount % num_winners
                        distributed_total = 0
                        print(f"DEBUG MM: Winner(s) ({winning_rank_obj.rank_name}): {winners}. Splitting pot {main_pot_amount} -> {win_amount_each} each.")
                        if remainder > 0: print(f"DEBUG MM: Remainder of {remainder} chips from split.")
                        for winner_name in winners:
                            self.players[winner_name]['chips'] += win_amount_each
                            distributed_total += win_amount_each
                        winner_info['win_amount'] = win_amount_each
                        winner_info['distributed_pot'] = distributed_total
                    else:
                        print("Warning MM: Showdown occurred but no winner determined from evaluated hands?")
                        winner_info['distributed_pot'] = 0
                else:
                    print("Warning MM: Showdown occurred but no hands were successfully evaluated.")
                    winner_info['distributed_pot'] = 0

            # --- <<< Heart Deduction Logic (MODIFIED) >>> ---
            human_state = self.players.get(self.human_player_name)
            if human_state:
                start_hearts = human_state.get('start_round_hearts')
                current_chips = human_state['chips'] # Chips *after* potential pot winnings
                current_hearts = human_state['hearts'] # Hearts *before* potential deduction below
                human_lost_round = self.human_player_name not in winner_info['winners']
                human_folded = human_state.get('folded')

                print(f"DEBUG MM Heart Check (End of Round): Player={self.human_player_name}, Lost={human_lost_round}, Folded={human_folded}, StartH={start_hearts}, CurrentH={current_hearts}, Chips={current_chips}")

                # Deduct heart ONLY IF: Human lost, DID NOT fold, had hearts at start, and hearts didn't change via exchange
                # REMOVED: current_chips > 0 check - deduction happens even if chips are now 0
                if human_lost_round and not human_folded and start_hearts is not None and start_hearts > 0:
                    if current_hearts == start_hearts: # Ensure heart wasn't already exchanged this cycle
                        human_state['hearts'] = max(0, current_hearts - 1)
                        print(f"DEBUG MM: Heart deducted (lost round AND did not fold) for {self.human_player_name}. StartH: {start_hearts}, New CurrentH: {human_state['hearts']}")
                    else:
                        print(f"DEBUG MM: Heart deduction skipped for {self.human_player_name} (lost round, not folded) because hearts changed during round (StartH:{start_hearts}, CurrentH:{current_hearts}). Exchange likely occurred.")
                elif human_folded:
                    print(f"DEBUG MM: Heart deduction skipped for {self.human_player_name} because player folded.")
                elif human_lost_round:
                    print(f"DEBUG MM: Human lost round, but no heart deduction possible/needed (already 0 hearts, or folded, or exchange happened).")
                else:
                    print(f"DEBUG MM: Human ({self.human_player_name}) won or tied, no heart deduction.")
            # --- <<< End Heart Deduction Logic >>> ---

        except Exception as e:
             print(f"ERROR MM: Exception during winner determination/payout: {e}")
             traceback.print_exc()
             winner_info['winners'] = []
             winner_info['distributed_pot'] = 0

        finally:
             self.pot = 0
             print(f"DEBUG MM: Winner determination function finished. Winners: {winner_info.get('winners')}. Distributed: {winner_info.get('distributed_pot')}")
             return winner_info


    def get_bot_action_gui(self, bot_name):
        """Gets action from the specified bot via its BotPlayer instance.
           Returns (action_string, amount). Amount is TOTAL bet for raise, 0 otherwise."""
        player_state = self.players.get(bot_name)
        if not player_state or not player_state.get('is_bot'):
            print(f"ERROR MM: get_bot_action called for invalid/non-bot player: {bot_name}")
            return "fold", 0 # Fold on error

        bot_player_instance = player_state.get('bot_instance')
        if not bot_player_instance:
             print(f"ERROR MM: Bot instance not found for {bot_name}.")
             return "fold", 0

        # Prepare a safe copy of the game state summary for the bot
        # Bots should generally not have access to modify the core game state directly
        game_state_for_bot = self.get_game_state_summary()
        # Add bot's own hole cards (not usually in the public summary)
        game_state_for_bot['my_cards'] = player_state.get('cards', [])
        # Optionally add other info bots might need (e.g., hand history, opponent modeling data)

        try:
            # Call the bot's decision-making method
            action, amount = bot_player_instance.get_action(game_state_for_bot)
            print(f"DEBUG MM: Bot {bot_name} chose action: {action}, amount: {amount}")

            # --- Basic Validation of Bot Action (optional but recommended) ---
            amount_to_call = max(0, self.current_bet - player_state['current_round_bet'])
            player_chips = player_state['chips']

            # Correct illegal check
            if action == "check" and amount_to_call > 0:
                print(f"Warning MM: Bot {bot_name} tried to check illegally. Forcing fold.")
                action = "fold"; amount = 0
            # Correct call to check if possible
            elif action == "call" and amount_to_call <= 0:
                action = "check"; amount = 0
            # Ensure raise amount is somewhat sane (Bot AI should handle min raise, but add basic checks)
            elif action == "raise":
                 target_total_bet = amount
                 chips_needed = target_total_bet - player_state['current_round_bet']
                 if chips_needed <= 0:
                     print(f"Warning MM: Bot {bot_name} invalid raise (amount <= current bet). Forcing check/fold.")
                     action = "check" if amount_to_call <= 0 else "fold"; amount = 0
                 elif chips_needed > player_chips:
                      print(f"Warning MM: Bot {bot_name} tried to raise more chips than available. Treating as All In.")
                      action = "all in"; amount = 0 # Amount ignored for all-in process step
            # Ensure all-in is valid
            elif action == "all in":
                 amount = 0 # Amount param not used by process_action for all-in

            # --- End Validation ---

            return action, amount

        except Exception as e:
            print(f"ERROR MM: Error getting action from bot {bot_name}: {e}")
            traceback.print_exc()
            return "fold", 0 # Fold on error


    def check_game_over_status(self):
        """Checks game end conditions (human hearts/chips, general chip counts).
           Handles heart exchange for the human player.
           Returns tuple: (is_over, message, reason)"""

        # 1. Check if already handled
        if self.game_over_handled:
            return True, "Game Over", getattr(self, '_game_over_reason', 'handled')
        # 2. Check if already flagged (but not handled)
        if self.game_over:
            # Ensure it gets handled now if we reach here
            print("DEBUG MM: check_game_over found game_over=True but not handled. Handling now.")
            self.game_over_handled = True
            return True, "Game Over", getattr(self, '_game_over_reason', 'unknown')

        human_player = self.players.get(self.human_player_name)
        exchange_occurred_this_check = False
        self._human_exchanged_heart_flag = False # Reset internal flag at the start of THIS check

        # --- Check Human Player Status FIRST ---
        if human_player:
            current_chips = human_player['chips']
            current_hearts = human_player['hearts']

            # Scenario A: Human has exactly 0 chips
            if current_chips == 0: # Changed from <= 0 for clarity
                print(f"DEBUG MM: CheckGameOver - Human {self.human_player_name} has 0 chips.")
                if current_hearts > 0: # Hearts available for exchange?
                    start_h = current_hearts # Hearts before exchange
                    human_player['hearts'] -= 1
                    human_player['chips'] += HEART_CHIP_EXCHANGE_AMOUNT
                    exchange_occurred_this_check = True
                    self._human_exchanged_heart_flag = True # <<< SET FLAG HERE for logging
                    print(f"DEBUG MM: CheckGameOver - Exchanged 1 heart. Hearts: {start_h}->{human_player['hearts']}. Chips: 0->{human_player['chips']}")
                    # Game continues for now after exchange
                else: # No hearts, no chips -> GAME OVER (Busted)
                    # This case is now correctly reached after the last heart was deducted in determine_winner_gui
                    print(f"DEBUG MM: CheckGameOver - Human {self.human_player_name} BUSTED (0 chips, 0 hearts).")
                    self.game_over = True; self._game_over_reason = 'busted'
                    self.game_over_handled = True # Mark handled immediately
                    return True, f"{self.human_player_name} has no chips and no hearts left!", 'busted'

            # Scenario B: Human has chips, but ran out of hearts (could be from deduction in determine_winner_gui)
            elif current_hearts <= 0: # Use <= 0 to catch if somehow it went negative
                 print(f"DEBUG MM: CheckGameOver - Human {self.human_player_name} has 0 hearts (but has {current_chips} chips).")
                 self.game_over = True; self._game_over_reason = 'hearts'
                 self.game_over_handled = True # Mark handled immediately
                 return True, f"{self.human_player_name}, you have lost all your hearts!", 'hearts'

        # --- Check General Chip Counts (Only if Human is okay OR round just ended) ---
        # This check is particularly relevant after pot distribution.
        # Let's ensure the round is actually marked as over before declaring winner based on chip counts.
        if self.round_over:
            players_with_chips = [name for name, p in self.players.items() if p['chips'] > 0]
            if len(players_with_chips) == 1:
                winner_name = players_with_chips[0]
                print(f"DEBUG MM: CheckGameOver (Post-Round) - {winner_name} is only player with chips.")
                if not self.game_over: # Only set if not already game over for other reasons
                    self.game_over = True
                    self._game_over_reason = 'chips'
                    self.game_over_handled = True
                    return True, f"{winner_name} wins! All Bots are out of chips.", 'chips'
                else:
                    return True, "Game Over", self._game_over_reason # Return existing reason

            elif len(players_with_chips) == 0:
                 print("DEBUG MM: CheckGameOver (Post-Round) - No players have chips left.")
                 if not self.game_over:
                     self.game_over = True
                     self._game_over_reason = 'no_chips'
                     self.game_over_handled = True
                     return True, "Game Over! No players have any chips left.", 'no_chips'
                 else:
                      return True, "Game Over", self._game_over_reason # Return existing reason

        # --- Game Continues ---
        if not self.game_over:
            print(f"DEBUG MM: CheckGameOver - Game continues. Exchange Occurred: {exchange_occurred_this_check}, RoundOverFlag: {self.round_over}")
            return False, None, None # is_over = False
        else:
             # Game is over, but was caught by initial checks - return True
             if not self.game_over_handled: self.game_over_handled = True
             return True, "Game Over", self._game_over_reason