this_state:     **start_of_round**
action:         choose optional action (Use Privilege, then Replenish Board if available), or proceed to mandatory action
next_state:     [use_privilege, replenish_board, choose_mandatory_action]

this_state:     **use_privilege**
action:         select token to take (cannot be gold)
effect:         gain token, lose privilege
next_state:     [start_of_round]  # can use privilege again or choose another action

this_state:     **replenish_board**
action:         confirm/cancel
condition:      only available if bag is not empty and after all desired privilege uses
effect:         refill board, opponent gains privilege
next_state:     [choose_mandatory_action]

this_state:     **choose_mandatory_action**
action:         choose one mandatory action (purchase_card, take_tokens, take_gold_and_reserve)
condition:      if no mandatory actions available, must replenish_board
next_state:     [purchase_card, take_tokens, take_gold_and_reserve]

this_state:     **purchase_card**
action:         select card to purchase (from eligible cards)
effect:         pay cost, gain card, resolve card ability, check for royal
next_state:     [post_action_checks]

this_state:     **take_tokens**
action:         select up to 3 eligible tokens (adjacent, non-gold, live checking)
effect:         gain tokens, opponent may gain privilege (if 3 same color or 2 pearls)
next_state:     [post_action_checks]

this_state:     **take_gold_and_reserve**
action:         select gold token and card to reserve (if eligible)
effect:         gain gold, reserve card
next_state:     [post_action_checks]

this_state:     **post_action_checks**
action:         discard down to 10 tokens if needed, check for victory
next_state:     [confirm_round]

this_state:     **confirm_round**
action:         confirm/cancel round end
effect:         finish round (switch player, new start_of_round) or rollback to start_of_round
next_state:     [start_of_round]


