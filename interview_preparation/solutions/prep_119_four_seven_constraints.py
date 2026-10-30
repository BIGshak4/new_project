"""The edited promise is x in {4,7}; the repeated original 4->7 is archived."""


def conditional(x):
    if x == 4:
        return 7
    return 4


def addition_subtraction(x):
    return 11 - x


def without_add_subtract_if(x):
    # Exact on both legal inputs. No rounding occurs on the promised domain.
    return 28 // x


def xor_only(x):
    return x ^ 3
