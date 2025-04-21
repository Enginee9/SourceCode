import random

class BotPlayer:
    def __init__(self, name, initial_chips, initial_hearts):
        self.name = name
        self.chips = initial_chips
        self.hearts = initial_hearts
        self.difficulty = "easy" # Default difficulty
        self.cards = [] # Bots might need to know their own cards internally

    def get_action(self, game_state):
        """
        Decides the bot's action based on game state and difficulty.
        game_state is a dictionary provided by MatchManager_GUI.get_game_state_summary().
        Returns: (action_string, amount)
        Amount is the TOTAL bet for a raise, 0 otherwise.
        """
        my_state = game_state['players'].get(self.name)
        if not my_state or my_state['folded'] or my_state['all_in']:
            return "fold", 0 # Should not be asked for action if folded/all-in

        current_bet = game_state['current_bet']
        my_bet_this_round = my_state['current_round_bet']
        amount_to_call = max(0, current_bet - my_bet_this_round)
        my_chips = my_state['chips']

        # --- Simple Bot Logic (Example - Replace with actual AI) ---

        can_check = amount_to_call <= 0

        # Basic "Easy" logic:
        if self.difficulty == "easy":
            # Check if possible
            if can_check:
                # 70% chance to check, 30% chance to bet small (if allowed)
                if random.random() < 0.7:
                    return "check", 0
                else:
                    # Try a small bet (e.g., big blind amount) if possible
                    big_blind = game_state.get('big_blind', 20) # Need BB info from game state
                    potential_bet = my_bet_this_round + big_blind
                    if my_chips >= big_blind:
                        # Basic raise validation (ensure it's a valid raise amount)
                        min_raise_increment = max(big_blind, current_bet - game_state.get('previous_bet', 0))
                        min_total_bet = current_bet + min_raise_increment
                        if potential_bet >= min_total_bet:
                             return "raise", potential_bet
                        else: # Cannot make min raise, just check
                            return "check", 0
                    else: # Not enough chips to bet, just check
                        return "check", 0
            else:
                # Must call, raise, or fold
                # 60% chance to call, 10% chance raise (if possible), 30% fold
                rand_action = random.random()
                if rand_action < 0.6: # Call
                    call_amount = min(amount_to_call, my_chips)
                    action = "call" if call_amount < my_chips else "all in"
                    return action, 0 # Amount is 0 for call/all-in handled by process_action
                elif rand_action < 0.7: # Try Raise (if possible)
                    big_blind = game_state.get('big_blind', 20)
                    # Min raise amount
                    min_raise_increment = max(big_blind, current_bet - game_state.get('previous_bet', 0))
                    min_total_bet = current_bet + min_raise_increment
                    chips_needed_for_min_raise = min_total_bet - my_bet_this_round

                    if my_chips >= chips_needed_for_min_raise:
                        # Raise minimum amount
                        return "raise", min_total_bet
                    else: # Cannot afford min raise, fallback to call
                        call_amount = min(amount_to_call, my_chips)
                        action = "call" if call_amount < my_chips else "all in"
                        return action, 0
                else: # Fold
                    return "fold", 0

        # --- Add "Hard" logic here ---
        elif self.difficulty == "hard":
            # Implement more sophisticated logic using hand strength, pot odds, position etc.
            # Placeholder: Just calls or folds
            if amount_to_call > 0:
                if my_chips >= amount_to_call and random.random() < 0.8: # High chance to call
                     return "call", 0
                elif my_chips < amount_to_call and my_chips > 0: # Call all-in if must call
                     return "all in", 0
                else:
                    return "fold", 0
            else:
                 return "check", 0 # Just check if possible

        else: # Default fallback
             return "fold", 0