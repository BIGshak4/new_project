"""Evaluate finite postfix token lists over integers and binary +, -, *.

An integer token is an actual Python int, never bool. Operator tokens are
strings. No string eval, division, unary operator or input mutation is used.
"""


def evaluate_postfix(tokens):
    if not isinstance(tokens, (list, tuple)):
        raise ValueError("tokens must be a list or tuple")  # noqa: TRY004 - one documented invalid-input API
    stack = []
    for token in tokens:
        if type(token) is int:
            stack.append(token)
        elif token in ("+", "-", "*"):
            if len(stack) < 2:
                raise ValueError("binary operator requires two operands")
            right = stack.pop()
            left = stack.pop()
            if token == "+":
                result = left + right
            elif token == "-":
                result = left - right
            else:
                result = left * right
            stack.append(result)
        else:
            raise ValueError("unknown token")
    if len(stack) != 1:
        raise ValueError("exactly one complete expression is required")
    return stack[0]
