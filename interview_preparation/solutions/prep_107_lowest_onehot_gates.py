"""Basic-gate prefix mask; shifts/indexes only describe bit wiring in this model.

The proposed datapath has NOT, AND and OR, with no arithmetic component. Python
integer representation is a simulation convenience, not a physical gate count.
"""


def lowest_onehot(value, width):
    if type(width) is not int or width < 1:
        raise ValueError("width must be a positive integer")
    if type(value) is not int or not 0 <= value < (1 << width):
        raise ValueError("value must fit the declared unsigned width")
    lower_any = 0
    output = 0
    for index in range(width):
        input_bit = (value >> index) & 1
        output_bit = input_bit & (lower_any ^ 1)
        output |= output_bit << index
        lower_any |= input_bit
    return output
