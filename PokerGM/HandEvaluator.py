from collections import Counter

# Simple Rank Representation (for sorting) - Higher is better
class HandRank:
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

    RANK_NAMES = {
        0: "High Card", 1: "Pair", 2: "Two Pair", 3: "Three of a Kind",
        4: "Straight", 5: "Flush", 6: "Full House", 7: "Four of a Kind",
        8: "Straight Flush", 9: "Royal Flush"
    }

    def __init__(self, rank_type, kickers):
        self.rank_type = rank_type
        self.kickers = sorted(kickers, reverse=True) # Ensure kickers are sorted high to low
        self.rank_name = self.RANK_NAMES.get(rank_type, "Unknown")

    # Implement comparison methods (__lt__, __eq__, __gt__) based on rank_type then kickers
    def __eq__(self, other):
        return self.rank_type == other.rank_type and self.kickers == other.kickers

    def __lt__(self, other):
        if self.rank_type != other.rank_type:
            return self.rank_type < other.rank_type
        # Compare kickers one by one
        for k1, k2 in zip(self.kickers, other.kickers):
            if k1 != k2:
                return k1 < k2
        return False # They are equal

    def __gt__(self, other):
        if self.rank_type != other.rank_type:
            return self.rank_type > other.rank_type
        # Compare kickers one by one
        for k1, k2 in zip(self.kickers, other.kickers):
            if k1 != k2:
                return k1 > k2
        return False # They are equal


class HandEvaluator:

    def __init__(self):
        # Card ranks for internal comparison (Ace high/low handled in logic)
        self.rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        self.rank_map_rev = {v: k for k, v in self.rank_map.items()} # For converting back

    def _get_numeric_cards(self, cards):
        """Converts card strings ('Ah', 'Td') to numeric tuples [(14, 'h'), (10, 'd')]"""
        num_cards = []
        for card in cards:
             if len(card) == 2:
                 rank_char = card[0]
                 suit_char = card[1]
                 rank_num = self.rank_map.get(rank_char)
                 if rank_num:
                     num_cards.append({'rank': rank_num, 'suit': suit_char, 'str': card})
             else: # Handle 10 correctly if stored as '10h'
                 if len(card) == 3 and card.startswith('10'):
                     rank_num = 10
                     suit_char = card[2]
                     num_cards.append({'rank': rank_num, 'suit': suit_char, 'str': card})

        # Sort by rank descending for easier processing
        num_cards.sort(key=lambda x: x['rank'], reverse=True)
        return num_cards

    def evaluate_hand(self, hole_cards, community_cards):
        """
        Evaluates the best 5-card poker hand from the given hole and community cards.
        Returns a tuple: (HandRank object, list_of_best_5_card_strings)
        THIS IS A PLACEHOLDER - A real implementation is complex.
        """
        all_cards = list(hole_cards) + list(community_cards)
        if len(all_cards) < 5:
            # Cannot make a 5-card hand - return High Card based on available
            if not all_cards: return HandRank(HandRank.HIGH_CARD, []), []
            num_cards = self._get_numeric_cards(all_cards)
            kickers = [c['rank'] for c in num_cards]
            card_strs = [c['str'] for c in num_cards]
            return HandRank(HandRank.HIGH_CARD, kickers[:5]), card_strs[:5]


        # --- Placeholder Logic: Just returns High Card ---
        # You need to replace this with actual hand evaluation logic
        # for pairs, two pairs, straights, flushes, etc.
        # Consider using itertools.combinations to get all 5-card combos
        # from the 7 available cards.

        from itertools import combinations

        best_rank = HandRank(HandRank.HIGH_CARD, [0]) # Initialize with lowest possible rank
        best_5_card_combo_strs = []

        if len(all_cards) >= 5:
            num_all_cards = self._get_numeric_cards(all_cards)

            for combo_indices in combinations(range(len(num_all_cards)), 5):
                 current_5_card_combo = [num_all_cards[i] for i in combo_indices]
                 current_5_card_combo.sort(key=lambda x: x['rank'], reverse=True) # Sort combo high to low

                 # --- >>> INSERT ACTUAL 5-CARD EVALUATION LOGIC HERE <<< ---
                 # This logic determines if the combo is a pair, straight, flush etc.
                 # and calculates the HandRank object for this specific 5-card combo.
                 # Example: Check for Flush
                 suits = [c['suit'] for c in current_5_card_combo]
                 is_flush = len(set(suits)) == 1
                 # Example: Check for Straight (needs Ace low handling)
                 ranks = sorted([c['rank'] for c in current_5_card_combo], reverse=True)
                 is_straight = all(ranks[i] == ranks[0] - i for i in range(5))
                 # Ace low straight (A,2,3,4,5) -> ranks are [14, 5, 4, 3, 2]
                 is_ace_low_straight = ranks == [14, 5, 4, 3, 2]
                 if is_ace_low_straight: ranks = [5,4,3,2,1] # Treat Ace as 1 for ranking

                 # Example: Check for Pairs, Trips, Quads using Counter
                 rank_counts = Counter(r['rank'] for r in current_5_card_combo)
                 counts = sorted(rank_counts.values(), reverse=True)
                 is_quads = counts[0] == 4
                 is_full_house = counts == [3, 2]
                 is_trips = counts[0] == 3 and len(counts) > 1 and counts[1] == 1
                 is_two_pair = counts[0] == 2 and len(counts) > 1 and counts[1] == 2
                 is_pair = counts[0] == 2 and len(counts) > 1 and counts[1] == 1

                 # Determine rank type and kickers for THIS 5-card combo
                 combo_rank_type = HandRank.HIGH_CARD
                 combo_kickers = ranks # Default kickers

                 if is_flush and is_straight and ranks[0] == 14 : combo_rank_type = HandRank.ROYAL_FLUSH; combo_kickers = []
                 elif is_flush and is_straight : combo_rank_type = HandRank.STRAIGHT_FLUSH; combo_kickers = [ranks[0]] # Highest card in straight
                 elif is_ace_low_straight and is_flush: combo_rank_type = HandRank.STRAIGHT_FLUSH; combo_kickers=[5] # Ace-low straight flush kicker is 5
                 elif is_quads:
                      combo_rank_type = HandRank.FOUR_OF_A_KIND
                      quad_rank = [r for r,c in rank_counts.items() if c==4][0]
                      kicker = [r for r,c in rank_counts.items() if c==1][0]
                      combo_kickers = [quad_rank, kicker]
                 elif is_full_house:
                      combo_rank_type = HandRank.FULL_HOUSE
                      trip_rank = [r for r,c in rank_counts.items() if c==3][0]
                      pair_rank = [r for r,c in rank_counts.items() if c==2][0]
                      combo_kickers = [trip_rank, pair_rank]
                 elif is_flush:
                      combo_rank_type = HandRank.FLUSH
                      combo_kickers = ranks # Flush kickers are just the ranks
                 elif is_straight or is_ace_low_straight:
                      combo_rank_type = HandRank.STRAIGHT
                      combo_kickers = [ranks[0]] # Highest card in straight
                 elif is_trips:
                      combo_rank_type = HandRank.THREE_OF_A_KIND
                      trip_rank = [r for r,c in rank_counts.items() if c==3][0]
                      kickers = sorted([r for r,c in rank_counts.items() if c==1], reverse=True)
                      combo_kickers = [trip_rank] + kickers
                 elif is_two_pair:
                      combo_rank_type = HandRank.TWO_PAIR
                      pair_ranks = sorted([r for r,c in rank_counts.items() if c==2], reverse=True)
                      kicker = [r for r,c in rank_counts.items() if c==1][0]
                      combo_kickers = pair_ranks + [kicker]
                 elif is_pair:
                      combo_rank_type = HandRank.PAIR
                      pair_rank = [r for r,c in rank_counts.items() if c==2][0]
                      kickers = sorted([r for r,c in rank_counts.items() if c==1], reverse=True)
                      combo_kickers = [pair_rank] + kickers
                 else: # High Card
                      combo_rank_type = HandRank.HIGH_CARD
                      combo_kickers = ranks


                 # --- Compare this combo's rank with the current best ---
                 current_combo_rank_obj = HandRank(combo_rank_type, combo_kickers)
                 if current_combo_rank_obj > best_rank:
                     best_rank = current_combo_rank_obj
                     best_5_card_combo_strs = [c['str'] for c in current_5_card_combo]

                 # --- END OF ACTUAL 5-CARD EVALUATION LOGIC ---

        # Return the HandRank object of the best combo found and the card strings
        if not best_5_card_combo_strs: # Fallback if loop didn't run
             num_cards = self._get_numeric_cards(all_cards)
             kickers = sorted([c['rank'] for c in num_cards], reverse=True)[:5]
             card_strs = [c['str'] for c in num_cards][:5]
             best_rank = HandRank(HandRank.HIGH_CARD, kickers)
             best_5_card_combo_strs = card_strs


        print(f"DEBUG Eval: Best Rank Found: {best_rank.rank_name}, Kickers: {best_rank.kickers}, Hand: {best_5_card_combo_strs}")
        return best_rank, best_5_card_combo_strs
