# --- START OF FILE MatchManager_GUI.py ---

import random
# Make sure these files exist and contain the necessary classes
try:
    from Deck import Deck
    from HandEvaluator import HandEvaluator, HandRank # Import HandRank if needed for comparisons/logging
    from BotPlayer import BotPlayer
except ImportError as e:
    print(f"FATAL ERROR: Could not import necessary game components: {e}")
    print("Make sure Deck.py, HandEvaluator.py, BotPlayer.py are in the same directory.")
    raise

# Define constants
INITIAL_HEARTS = 1
HEART_CHIP_EXCHANGE_AMOUNT = 1000

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
        self.previous_bet = 0
        self.last_raiser = None
        self.current_stage = None
        self.round_over = False
        self.game_over = False
        self.game_over_handled = False
        self.small_blind = max(1, initial_chips // 100)
        self.big_blind = max(1, initial_chips // 50)
        if self.big_blind < self.small_blind * 2: self.big_blind = self.small_blind * 2
        print(f"DEBUG MM: Blinds calculated - SB: {self.small_blind}, BB: {self.big_blind}")

        self.turn_order_this_round = []
        self.current_player_turn_index = -1
        self._human_exchanged_heart_flag = False # Internal flag for logging
        self._player_action_count_this_betting_round = {} # Track actions per player in betting round
        self._aggressor_acted_this_cycle = False # Track if last raiser acted since raising

        # Add Human Player
        self.players[player_name] = {
            'chips': self.initial_chips, 'hearts': initial_hearts, 'cards': [],
            'current_round_bet': 0, 'total_round_investment': 0,
            'folded': False, 'all_in': False, 'is_bot': False,
            'start_round_chips': self.initial_chips, 'start_round_hearts': initial_hearts
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
                    'chips': self.initial_chips, 'hearts': initial_hearts, 'cards': [],
                    'current_round_bet': 0, 'total_round_investment': 0,
                    'folded': False, 'all_in': False, 'is_bot': True,
                    'bot_instance': bot_player,
                    'start_round_chips': self.initial_chips, 'start_round_hearts': initial_hearts
                }
                print(f"DEBUG MM: Added bot {bot_name} with {self.initial_chips} chips and {initial_hearts} hearts.")
            except Exception as e: print(f"ERROR MM: Failed to create/add bot {bot_name}: {e}"); import traceback; traceback.print_exc()

        # Initialize Dealer Button
        player_names = list(self.players.keys())
        if player_names: self.dealer_button_index = random.randrange(len(player_names)); self.dealer_button_player = player_names[self.dealer_button_index]; print(f"DEBUG MM: Initial dealer button set to {self.dealer_button_player}")
        else: self.dealer_button_index = -1; self.dealer_button_player = None; print("WARNING MM: No players found")

        try: self.hand_evaluator = HandEvaluator()
        except Exception as e: print(f"FATAL ERROR: Failed to initialize HandEvaluator: {e}"); raise
        print(f"DEBUG MM: PokerGame initialization complete.")

    def get_game_state_summary(self):
        """Returns a dictionary summarizing the current game state for the GUI."""
        players_summary = {}
        for name, p_state in self.players.items():
            players_summary[name] = {
                'chips': p_state.get('chips', 0), 'hearts': p_state.get('hearts', 0),
                'cards': p_state.get('cards', []), 'current_round_bet': p_state.get('current_round_bet', 0),
                'folded': p_state.get('folded', False), 'all_in': p_state.get('all_in', False),
                'is_bot': p_state.get('is_bot', False),
                 'start_round_chips': p_state.get('start_round_chips'),
                 'start_round_hearts': p_state.get('start_round_hearts')
            }

        current_turn_player = None
        if not self.round_over and self.turn_order_this_round and 0 <= self.current_player_turn_index < len(self.turn_order_this_round):
             current_turn_player = self.turn_order_this_round[self.current_player_turn_index]
             player_state = self.players.get(current_turn_player)
             # Log only if the reported turn player is unexpectedly ineligible
             if player_state and (player_state.get('folded') or player_state.get('all_in')):
                  print(f"WARN MM Summary: Reporting turn={current_turn_player}, but player state is folded/all_in.")

        return {
            'players': players_summary, 'community_cards': list(self.community_cards),
            'pot': self.pot, 'current_bet': self.current_bet, 'previous_bet': self.previous_bet,
            'current_stage': self.current_stage, 'dealer_button_player': self.dealer_button_player,
            'current_turn_player': current_turn_player,
            'small_blind': self.small_blind, 'big_blind': self.big_blind,
        }

    def start_new_round_get_info(self):
        """Resets round, deals, posts blinds, determines turn order."""
        print("\nDEBUG MM: --- Starting New Round ---")
        if self.game_over: return {'error': 'Game is already over.', 'game_over': True}

        # Check for bot bust condition
        bot_names = [b.name for b in self.bots]
        for bot_name in bot_names:
            if bot_name in self.players and self.players[bot_name].get('chips', 0) <= 0:
                print(f"DEBUG MM: StartNewRound - Bot '{bot_name}' has busted. Player wins!")
                self.game_over = True; self._game_over_reason = 'bot_bust'
                final_message = f"{self.human_player_name} wins! Bot {busted_bot_name} is out of chips." # Use busted_bot_name if needed
                # Correction: Assign busted bot name properly
                busted_bot_name = bot_name # Assign inside the loop when found
                final_message = f"{self.human_player_name} wins! Bot {busted_bot_name} is out of chips."
                return {'error': final_message, 'game_over': True}


        # Filter active players
        active_players_with_chips = [name for name, p in self.players.items() if p.get('chips', 0) > 0]
        if len(active_players_with_chips) <= 1:
             winner_name = active_players_with_chips[0] if active_players_with_chips else "No one"
             print(f"DEBUG MM: StartNewRound - Only {winner_name} has chips.")
             self.game_over = True; self._game_over_reason = 'chips'
             final_message = f"{winner_name} wins! All other players are out of chips." if active_players_with_chips else "Game over! No players have chips."
             return {'error': final_message, 'game_over': True}

        # Reset Round States
        self.deck.reset_and_shuffle()
        self.community_cards = []; self.pot = 0; self.current_bet = 0; self.previous_bet = 0
        self.last_raiser = None; self.round_over = False; self.current_stage = 'pre-flop'
        self._human_exchanged_heart_flag = False
        self._player_action_count_this_betting_round = {}
        self._aggressor_acted_this_cycle = False

        for name, player_state in self.players.items():
             self._player_action_count_this_betting_round[name] = 0
             if name in active_players_with_chips: player_state.update({'cards': [], 'current_round_bet': 0, 'total_round_investment': 0, 'folded': False, 'all_in': False, 'start_round_chips': player_state['chips'], 'start_round_hearts': player_state['hearts']})
             else: player_state.update({'folded': True, 'all_in': False})

        # Move Dealer Button
        current_dealer_idx_in_active = -1
        try:
             if self.dealer_button_player and self.dealer_button_player in active_players_with_chips: current_dealer_idx_in_active = active_players_with_chips.index(self.dealer_button_player)
             elif self.dealer_button_player:
                 original_player_list = list(self.players.keys()); search_start_idx = original_player_list.index(self.dealer_button_player)
                 for i in range(1, len(original_player_list) + 1):
                     next_idx = (search_start_idx + i) % len(original_player_list); next_player = original_player_list[next_idx]
                     if next_player in active_players_with_chips: effective_last_dealer_idx = active_players_with_chips.index(next_player) - 1; current_dealer_idx_in_active = effective_last_dealer_idx % len(active_players_with_chips); break
        except (ValueError, IndexError) as e: print(f"Warning MM: Error finding previous dealer '{self.dealer_button_player}': {e}"); current_dealer_idx_in_active = -1
        if current_dealer_idx_in_active == -1: current_dealer_idx_in_active = random.randrange(len(active_players_with_chips)) - 1; current_dealer_idx_in_active = max(-1, current_dealer_idx_in_active) % len(active_players_with_chips)
        new_dealer_idx_in_active = (current_dealer_idx_in_active + 1) % len(active_players_with_chips)
        self.dealer_button_player = active_players_with_chips[new_dealer_idx_in_active]
        self.dealer_button_index = list(self.players.keys()).index(self.dealer_button_player)
        print(f"DEBUG MM: Dealer button moved to {self.dealer_button_player}")

        # Determine Blinds
        num_active = len(active_players_with_chips); sb_idx = (new_dealer_idx_in_active + 1) % num_active; bb_idx = (new_dealer_idx_in_active + 2) % num_active
        if num_active == 2: sb_idx, bb_idx = new_dealer_idx_in_active, (new_dealer_idx_in_active + 1) % num_active
        sb_player, bb_player = active_players_with_chips[sb_idx], active_players_with_chips[bb_idx]

        # Post Blinds
        sb_amount = self._post_bet(sb_player, self.small_blind); print(f"DEBUG MM: {sb_player} posts SB {sb_amount}")
        bb_amount = self._post_bet(bb_player, self.big_blind); print(f"DEBUG MM: {bb_player} posts BB {bb_amount}")
        self.current_bet = self.big_blind; self.previous_bet = 0

        # Deal Hole Cards
        try:
            for _ in range(2):
                for name in active_players_with_chips:
                     card = self.deck.deal_card();
                     if not card: raise ValueError("Deck empty")
                     self.players[name]['cards'].append(card)
        except ValueError as e: return {'error': f'{e} during deal.', 'game_over': True}

        # Determine Turn Order
        first_act_idx = (bb_idx + 1) % num_active
        if num_active == 2: first_act_idx = sb_idx
        self.turn_order_this_round = active_players_with_chips[first_act_idx:] + active_players_with_chips[:first_act_idx]
        self.last_raiser = bb_player

        # Find first player to act
        self.current_player_turn_index = -1
        for i, name in enumerate(self.turn_order_this_round):
             if not self.players[name].get('all_in'): self.current_player_turn_index = i; break
        if self.current_player_turn_index == -1 and self.turn_order_this_round: self.current_player_turn_index = 0

        print(f"DEBUG MM: Pre-flop turn order: {self.turn_order_this_round}")
        if self.turn_order_this_round and self.current_player_turn_index != -1: print(f"DEBUG MM: Starting turn index: {self.current_player_turn_index} ({self.turn_order_this_round[self.current_player_turn_index]})")
        else: print("DEBUG MM: No valid starting turn player.")

        return {
            'turn_order': list(self.turn_order_this_round), 'start_index': self.current_player_turn_index,
            'dealer': self.dealer_button_player, 'sb_player': sb_player, 'sb_amount': sb_amount,
            'bb_player': bb_player, 'bb_amount': bb_amount
        }

    def _post_bet(self, player_name, amount):
        """Helper to post a bet/blind and update state."""
        player = self.players[player_name]
        actual_amount = min(amount, player['chips'])
        player['chips'] -= actual_amount
        player['current_round_bet'] += actual_amount
        player['total_round_investment'] += actual_amount
        self.pot += actual_amount
        if player['chips'] == 0:
            player['all_in'] = True
            print(f"DEBUG MM:_post_bet {player_name} is All In for {actual_amount}")
        return actual_amount

    def _advance_turn_index(self):
        """Finds the NEXT player in order who can act."""
        if not self.turn_order_this_round: self.current_player_turn_index = -1; return -1
        num_players = len(self.turn_order_this_round)
        if num_players == 0: return -1

        original_index = self.current_player_turn_index
        if original_index < 0 or original_index >= num_players: original_index = -1

        for i in range(1, num_players + 1):
            next_index = (original_index + i) % num_players
            next_player_name = self.turn_order_this_round[next_index]
            player_state = self.players.get(next_player_name)
            if player_state and not player_state.get('folded') and not player_state.get('all_in'):
                self.current_player_turn_index = next_index
                print(f"DEBUG MM: Advanced turn index from {original_index} to {next_index} ({next_player_name})")
                return self.current_player_turn_index

        print("Warning MM: _advance_turn_index looped - no eligible player found.")
        self.current_player_turn_index = -1
        return -1

    def process_player_action(self, player_name, action, amount=0):
        """Processes action & advances internal turn index."""
        if self.round_over or self.game_over: return
        player = self.players.get(player_name)

        current_player_expected = None
        if self.turn_order_this_round and 0 <= self.current_player_turn_index < len(self.turn_order_this_round):
            current_player_expected = self.turn_order_this_round[self.current_player_turn_index]
        if current_player_expected != player_name:
             print(f"ERROR MM: process_player_action called for {player_name} but internal index points to {current_player_expected}")
             return

        if not player or player['folded'] or player['all_in']:
            print(f"Warning MM: process_player_action called for ineligible player {player_name}. Advancing index.")
            self._advance_turn_index(); return

        print(f"DEBUG MM: Processing action: {player_name}, {action}, Amount:{amount}")
        amount_to_call = self.current_bet - player['current_round_bet']
        self._player_action_count_this_betting_round[player_name] = self._player_action_count_this_betting_round.get(player_name, 0) + 1
        if player_name == self.last_raiser: self._aggressor_acted_this_cycle = True

        try:
            if action == "fold": player['folded'] = True; print(f"DEBUG MM: {player_name} folded."); self._check_round_end_condition()
            elif action == "check":
                if amount_to_call > 0: raise ValueError(f"{player_name} cannot check.")
                print(f"DEBUG MM: {player_name} checked.")
            elif action == "call":
                if amount_to_call > 0: call_cost = self._post_bet(player_name, amount_to_call); print(f"DEBUG MM: {player_name} called {call_cost}.")
                else: print(f"Warning MM: {player_name} called when check possible.")
            elif action == "raise":
                 chips_needed = amount - player['current_round_bet']
                 if chips_needed <= 0: raise ValueError("Raise amount must result in a higher total bet.")
                 is_all_in_raise = chips_needed >= player['chips']
                 actual_raise_cost = min(chips_needed, player['chips'])
                 min_raise_inc = max(self.big_blind, self.current_bet - self.previous_bet)
                 min_legal_bet = self.current_bet + min_raise_inc
                 if not is_all_in_raise and amount < min_legal_bet: raise ValueError(f"Raise target ({amount}) < min ({min_legal_bet}).")
                 if actual_raise_cost <= 0: raise ValueError("Cannot raise with zero cost.")
                 if actual_raise_cost > player['chips'] + 0.01 : raise ValueError(f"Insufficient chips ({player['chips']}) for raise cost ({actual_raise_cost}).")
                 self._post_bet(player_name, actual_raise_cost)
                 self.previous_bet = self.current_bet; self.current_bet = player['current_round_bet']; self.last_raiser = player_name
                 self._player_action_count_this_betting_round = {p: 0 for p in self.players}; self._player_action_count_this_betting_round[player_name] = 1
                 self._aggressor_acted_this_cycle = True
                 print(f"DEBUG MM: {player_name} raised to {self.current_bet} (+{actual_raise_cost}).")
            elif action == "all in":
                all_in_cost = player['chips']
                if all_in_cost <= 0: print(f"Warning MM: {player_name} all-in with 0 chips."); raise ValueError("All-in with no chips")
                self._post_bet(player_name, all_in_cost)
                print(f"DEBUG MM: {player_name} went All In for {all_in_cost}.")
                if player['current_round_bet'] > self.current_bet:
                     print(f"DEBUG MM: All-in by {player_name} raises bet.")
                     self.previous_bet = self.current_bet; self.current_bet = player['current_round_bet']; self.last_raiser = player_name
                     self._player_action_count_this_betting_round = {p: 0 for p in self.players}; self._player_action_count_this_betting_round[player_name] = 1
                     self._aggressor_acted_this_cycle = True
            else: print(f"Warning MM: Unknown action: {action}")
        except ValueError as e: print(f"ERROR MM: Action processing error - {e}"); raise
        finally:
            if not self.round_over: self._advance_turn_index()

    def _check_round_end_condition(self):
        """Checks if only one player remains active (not folded)."""
        not_folded_players = [name for name, p in self.players.items() if not p.get('folded')]
        if len(not_folded_players) <= 1:
             print(f"DEBUG MM: Round ending early, <=1 player not folded ({not_folded_players}).")
             self.round_over = True

    def is_betting_over(self):
        """Checks if the current betting round is complete."""
        if self.round_over: return True

        contesting_players = {name: p for name, p in self.players.items() if not p.get('folded')}
        if len(contesting_players) < 2:
            print("DEBUG MM: is_betting_over: True (<=1 player contesting)")
            return True

        eligible_actors = [name for name, p in contesting_players.items() if not p.get('all_in')]
        if len(eligible_actors) == 0: # All remaining players are all-in
             print(f"DEBUG MM: is_betting_over: True (All {len(contesting_players)} contesting players are all-in)")
             return True
        elif len(eligible_actors) == 1: # Only one player left who can bet
             # Check pre-flop BB option
             is_preflop = self.current_stage == 'pre-flop'
             if is_preflop and self.current_bet <= self.big_blind:
                  bb_player = self.last_raiser # Initial aggressor pre-flop
                  if eligible_actors[0] == bb_player and self._player_action_count_this_betting_round.get(bb_player, 0) < 1:
                       print("DEBUG MM: is_betting_over: False (Pre-flop BB option available)")
                       return False
             print(f"DEBUG MM: is_betting_over: True (Only 1 eligible actor left: {eligible_actors[0]})")
             return True

        # Multiple players can still act. Check if they have all acted and matched.
        all_acted_this_cycle = True
        all_bets_matched = True

        if not self.turn_order_this_round: # Safety check
             print("ERROR MM: is_betting_over called with empty turn_order!")
             return True # Assume over if state is inconsistent

        for name in self.turn_order_this_round:
            player_state = self.players.get(name)
            if player_state and not player_state.get('folded'):
                if not player_state.get('all_in'): # Only check players who can act
                    if self._player_action_count_this_betting_round.get(name, 0) < 1:
                        all_acted_this_cycle = False
                        # print(f"DEBUG MM: is_betting_over: False ({name} hasn't acted this cycle)")
                        break
                    if player_state['current_round_bet'] < self.current_bet:
                        all_bets_matched = False
                        # print(f"DEBUG MM: is_betting_over: False ({name} bet {player_state['current_round_bet']} < current {self.current_bet})")
                        break

        # If loop finished without breaking, check conditions
        if all_acted_this_cycle and all_bets_matched:
             print(f"DEBUG MM: is_betting_over: True (All acted & matched at {self.current_bet})")
             return True

        print(f"DEBUG MM: is_betting_over: False (Acted Cycle:{all_acted_this_cycle}, Matched:{all_bets_matched})")
        return False

    # ... (advance_to_next_stage, start_next_betting_round) ...
    # ... (determine_winner_gui, get_bot_action_gui, check_game_over_status) ...
    # ... (remain the same as previous version) ...
    def advance_to_next_stage(self):
        """Deals community cards or moves to Showdown."""
        if self.round_over or self.game_over: return None
        if not self.current_stage: return None

        print(f"DEBUG MM: Advancing stage from {self.current_stage}")
        next_stage_map = {'pre-flop': 'flop', 'flop': 'turn', 'turn': 'river', 'river': 'showdown'}
        card_deal_map = {'flop': 3, 'turn': 1, 'river': 1}

        if self.current_stage in next_stage_map:
            next_stage = next_stage_map[self.current_stage]
            self.current_stage = next_stage

            if next_stage == 'showdown':
                self.round_over = True
                print("DEBUG MM: Moving to Showdown.")
                return 'showdown'
            else:
                # --- Reset action counts for the new betting round ---
                self._player_action_count_this_betting_round = {p: 0 for p in self.players}
                self._aggressor_acted_this_cycle = False # Reset flag
                # --- End Reset ---
                num_cards_to_deal = card_deal_map.get(next_stage, 0)
                if num_cards_to_deal > 0:
                     try:
                         self.deck.burn_card()
                         for _ in range(num_cards_to_deal):
                             card = self.deck.deal_card()
                             if card: self.community_cards.append(card)
                             else: raise ValueError("Deck empty during deal")
                         print(f"DEBUG MM: Dealt {next_stage.capitalize()}: {self.community_cards}")
                         return next_stage
                     except Exception as e:
                          print(f"ERROR MM: Failed to deal cards for {next_stage}: {e}")
                          self.game_over = True; self._game_over_reason = 'deck_error'
                          return None
        else:
            print(f"Warning MM: Cannot advance stage from unknown stage: {self.current_stage}")
            return None

    def start_next_betting_round(self):
        """Resets betting vars & determines turn order for Flop/Turn/River."""
        if self.round_over or self.game_over: return {'turn_order': [], 'start_index': -1}
        if self.current_stage == 'pre-flop':
             print("Warning MM: start_next_betting_round called pre-flop."); # Should be handled by advance_stage
             return {'turn_order': list(self.turn_order_this_round), 'start_index': self.current_player_turn_index}

        print(f"DEBUG MM: Starting next betting round for stage: {self.current_stage}")
        self.current_bet = 0; self.previous_bet = 0; self.last_raiser = None
        self._aggressor_acted_this_cycle = False # Reset flag

        # Reset action counts AND current bets for players still in
        contesting_players = []
        original_order = list(self.players.keys())
        for name in original_order:
            player_state = self.players[name]
            self._player_action_count_this_betting_round[name] = 0 # Reset action count
            if not player_state.get('folded'):
                 contesting_players.append(name)
                 if not player_state.get('all_in'):
                     player_state['current_round_bet'] = 0 # Reset bet

        if not contesting_players:
             print("Warning MM: No contesting players for next betting round."); self.round_over = True
             return {'turn_order': [], 'start_index': -1}

        # Determine turn order: starts left of the dealer button among contesting players
        dealer_idx_original = -1
        if self.dealer_button_player in original_order: dealer_idx_original = original_order.index(self.dealer_button_player)
        first_actor_name = None
        for i in range(len(original_order)):
             check_idx = (dealer_idx_original + 1 + i) % len(original_order)
             check_name = original_order[check_idx]
             if check_name in contesting_players: first_actor_name = check_name; break
        if not first_actor_name: first_actor_name = contesting_players[0] # Fallback

        start_idx_in_contesting = contesting_players.index(first_actor_name)
        self.turn_order_this_round = contesting_players[start_idx_in_contesting:] + contesting_players[:start_idx_in_contesting]

        # Find the first player in the new order who is NOT all-in
        self.current_player_turn_index = -1
        for i, name in enumerate(self.turn_order_this_round):
             if not self.players[name].get('all_in'): self.current_player_turn_index = i; break

        if self.current_player_turn_index == -1:
             print("DEBUG MM: All remaining players are all-in post-flop. No betting.")
             self.turn_order_this_round = []
             return {'turn_order': [], 'start_index': -1}

        print(f"DEBUG MM: New turn order for {self.current_stage}: {self.turn_order_this_round}")
        print(f"DEBUG MM: Starting turn index: {self.current_player_turn_index} ({self.turn_order_this_round[self.current_player_turn_index]})")

        return {'turn_order': list(self.turn_order_this_round), 'start_index': self.current_player_turn_index}


    def determine_winner_gui(self):
        """Determines winner(s), awards pot(s), handles heart deduction."""
        print("DEBUG MM: Determining winner...")
        if not self.round_over:
            print("Warning MM: determine_winner called but round is not over.")
            return None # Indicate error or unexpected state

        winner_info = {'winners': [], 'pot': self.pot, 'details': {}, 'win_amount': 0}
        try:
            # --- SIDE POT CALCULATION NEEDED HERE ---
            # This simplified version ignores side pots and assumes one main pot.

            main_pot_amount = self.pot # Use total pot in simplified version
            winner_info['distributed_pot'] = main_pot_amount # Store amount distributed

            # Identify players eligible for the (simplified) main pot
            eligible_players = {name: p for name, p in self.players.items() if not p.get('folded')}

            if len(eligible_players) == 1:
                winner_name = list(eligible_players.keys())[0]
                winner_info['winners'] = [winner_name]
                winner_info['details'][winner_name] = {'type': 'Default (Others Folded)', 'hole_cards': self.players[winner_name]['cards']}
                win_amount = main_pot_amount
                winner_info['win_amount'] = win_amount
                self.players[winner_name]['chips'] += win_amount
                print(f"DEBUG MM: {winner_name} wins {win_amount} by default.")

            elif len(eligible_players) > 1:
                # Showdown evaluation
                best_hands = {}
                evaluated_details = {}
                for name, player_state in eligible_players.items():
                     hole_cards = player_state.get('cards', [])
                     if not hole_cards: continue # Skip players with no cards

                     # Evaluate hand using HandEvaluator
                     try:
                         rank, best_5_cards = self.hand_evaluator.evaluate_hand(hole_cards, self.community_cards)
                         if rank is not None:
                             best_hands[name] = rank # Store HandRank object for comparison
                             evaluated_details[name] = {'type': rank.rank_name, 'hand': best_5_cards, 'hole_cards': hole_cards}
                             print(f"DEBUG MM: {name} evaluated: {rank.rank_name} - {best_5_cards}")
                         else:
                              evaluated_details[name] = {'type': 'Eval Error', 'hole_cards': hole_cards}
                     except Exception as e:
                          print(f"ERROR MM: Hand evaluation failed for {name}: {e}")
                          evaluated_details[name] = {'type': 'Eval Exception', 'hole_cards': hole_cards}
                winner_info['details'] = evaluated_details # Store all eval details

                # Find the winning rank(s)
                if best_hands:
                    winning_rank_obj = max(best_hands.values())
                    winners = [name for name, rank_obj in best_hands.items() if rank_obj == winning_rank_obj]
                    winner_info['winners'] = winners

                    if winners:
                        win_amount_each = main_pot_amount // len(winners) # Simple split
                        winner_info['win_amount'] = win_amount_each
                        print(f"DEBUG MM: Winners ({winning_rank_obj.rank_name}): {winners}. Splitting pot {main_pot_amount} -> {win_amount_each} each.")
                        for winner_name in winners:
                            self.players[winner_name]['chips'] += win_amount_each
                    else: print("Warning MM: Showdown occurred but no winner determined?")
                else: print("Warning MM: Showdown occurred but no hands successfully evaluated?")

            else: print("Warning MM: No eligible players found at end of round.")

            # --- Heart Deduction Logic (Runs AFTER pot distribution) ---
            human_state = self.players.get(self.human_player_name)
            if human_state:
                start_hearts = human_state.get('start_round_hearts')
                current_chips = human_state['chips']
                human_lost_round = self.human_player_name not in winner_info['winners']

                # Deduct heart ONLY if human lost round AND finished with chips > 0
                if human_lost_round and start_hearts is not None and start_hearts > 0 and current_chips > 0:
                     if human_state['hearts'] == start_hearts: # Check heart wasn't already changed
                         human_state['hearts'] = max(0, human_state['hearts'] - 1)
                         print(f"DEBUG MM: Heart deducted (lost round, >0 chips) for {self.human_player_name}. StartH: {start_hearts}, EndH: {human_state['hearts']}")
                     # else: print(f"DEBUG MM: Heart logic skipped (lost round, >0 chips) - hearts mismatch.") # Less noisy log
                elif human_lost_round:
                     print(f"DEBUG MM: Human lost round, but chips are <= 0 ({current_chips}). Heart logic handled by check_game_over.")

        except Exception as e:
             print(f"ERROR MM: Exception during winner determination/payout: {e}")
             import traceback; traceback.print_exc()
             # Pot might be lost or handled incorrectly on error

        finally:
             # --- Reset pot AFTER attempting distribution ---
             self.pot = 0
             print(f"DEBUG MM: Winner determination function finished. Winners: {winner_info.get('winners')}")
             return winner_info


    def get_bot_action_gui(self, bot_name):
        """Gets action from the specified bot."""
        player_state = self.players.get(bot_name)
        if not player_state or not player_state.get('is_bot'):
            print(f"ERROR MM: get_bot_action called for invalid bot: {bot_name}")
            return "fold", 0 # Fold on error

        bot_player_instance = player_state.get('bot_instance')
        if not bot_player_instance:
             print(f"ERROR MM: Bot instance not found for {bot_name}.")
             return "fold", 0

        # Prepare safe game state copy for the bot
        game_state_for_bot = self.get_game_state_summary()
        # Add bot's own cards (not usually in summary)
        game_state_for_bot['my_cards'] = player_state.get('cards', [])

        try:
            action, amount = bot_player_instance.get_action(game_state_for_bot)
            print(f"DEBUG MM: Bot {bot_name} chose action: {action}, amount: {amount}")

            # Basic validation of bot action before returning
            amount_to_call = self.current_bet - player_state['current_round_bet']
            if action == "check" and amount_to_call > 0: action = "fold" # Force fold if illegal check
            if action == "call" and amount_to_call <= 0: action = "check" # Correct call to check
            # Further validation could be added for raise amounts

            return action, amount
        except Exception as e:
            print(f"ERROR MM: Error getting action from bot {bot_name}: {e}")
            import traceback; traceback.print_exc()
            return "fold", 0


    def check_game_over_status(self):
        """Checks game end conditions (hearts, chips between rounds)."""
        if self.game_over_handled: return True, "Game Over", getattr(self, '_game_over_reason', 'handled')
        if self.game_over: return True, "Game Over", getattr(self, '_game_over_reason', 'unknown')

        human_player = self.players.get(self.human_player_name)
        exchange_occurred = False
        self._human_exchanged_heart_flag = False # Reset internal flag

        # --- Check Human Player Status FIRST ---
        if human_player:
            if human_player['chips'] <= 0: # Human ran out of chips this round
                print(f"DEBUG MM: CheckGameOver - Human {self.human_player_name} has 0 chips.")
                if human_player['hearts'] > 0: # Hearts available for exchange?
                    start_h = human_player['hearts']
                    human_player['hearts'] -= 1
                    human_player['chips'] += HEART_CHIP_EXCHANGE_AMOUNT
                    exchange_occurred = True
                    self._human_exchanged_heart_flag = True # Set flag for GUI logging
                    print(f"DEBUG MM: CheckGameOver - Exchanged 1 heart. Hearts: {start_h}->{human_player['hearts']}. Chips: 0->{human_player['chips']}")
                    # Game continues
                else: # No hearts, no chips -> GAME OVER (Busted)
                    print(f"DEBUG MM: CheckGameOver - Human {self.human_player_name} BUSTED (0 chips, 0 hearts).")
                    self.game_over = True
                    self._game_over_reason = 'busted'
                    return True, f"{self.human_player_name} has no chips and no hearts left!", 'busted'

            # If chips > 0, check if hearts ran out
            elif human_player['hearts'] <= 0:
                 print(f"DEBUG MM: CheckGameOver - Human {self.human_player_name} has 0 hearts (but has chips).")
                 self.game_over = True
                 self._game_over_reason = 'hearts'
                 return True, f"{self.human_player_name}, you have lost all your hearts!", 'hearts'

        # --- Check General Chip Counts (Only AFTER a round is complete) ---
        if self.round_over:
            players_with_chips = [name for name, p in self.players.items() if p['chips'] > 0]
            if len(players_with_chips) == 1:
                winner_name = players_with_chips[0]
                print(f"DEBUG MM: CheckGameOver (Post-Round) - {winner_name} is only player with chips.")
                self.game_over = True
                self._game_over_reason = 'chips'
                return True, f"{winner_name} wins! All other players are out of chips.", 'chips'
            elif len(players_with_chips) == 0:
                 print("DEBUG MM: CheckGameOver (Post-Round) - No players have chips left.")
                 self.game_over = True
                 self._game_over_reason = 'no_chips'
                 return True, "Game Over! No players have any chips left.", 'no_chips'

        # --- Game Continues ---
        print(f"DEBUG MM: CheckGameOver - Game continues. Exchange: {exchange_occurred}, RoundOverFlag: {self.round_over}")
        return False, None, None # is_over = False


# --- END OF FILE MatchManager_GUI.py ---