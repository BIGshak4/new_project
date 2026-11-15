"""Finite verifier for a three-question strategy, not a learner execution profile."""
from itertools import permutations, product


def verify_strategy():
    transcripts = 0
    for roles in permutations(("Truth", "Lie", "Random")):
        for da_means_yes, coins in product((False, True), product((False, True), repeat=3)):
            used = 0

            def ask(person, proposition):
                nonlocal used
                # Ask: (P iff you are Truth) iff da means yes.
                statement = (proposition == (roles[person] == "Truth")) == da_means_yes
                if roles[person] == "Random":
                    da = coins[used]
                else:
                    yes = statement if roles[person] == "Truth" else not statement
                    da = yes == da_means_yes
                used += 1
                return da

            first = ask(0, roles[1] == "Random")
            reliable = 2 if first else 1
            assert roles[reliable] != "Random"
            if ask(reliable, roles[0] == "Random"):
                reliable_type = "Truth" if ask(reliable, roles[reliable] == "Truth") else "Lie"
                answer = [None, None, None]
                answer[0] = "Random"
                answer[reliable] = reliable_type
                answer[3 - reliable] = "Lie" if reliable_type == "Truth" else "Truth"
            else:
                a_type = "Truth" if ask(reliable, roles[0] == "Truth") else "Lie"
                answer = [a_type, None, None]
                answer[reliable] = "Lie" if a_type == "Truth" else "Truth"
                answer[3 - reliable] = "Random"
            assert tuple(answer) == roles and used == 3
            transcripts += 1
    return transcripts
