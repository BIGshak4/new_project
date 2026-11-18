def evaluate_compact_postfix(expression):
    """Scan ASCII digits and binary + - * /; division truncates toward zero."""
    stack = []
    for symbol in expression:
        if symbol in ' \t\r\n':
            continue
        if '0' <= symbol <= '9':
            stack.append(ord(symbol) - ord('0'))
            continue
        if symbol not in '+-*/' or len(stack) < 2:
            raise ValueError('invalid postfix operator or missing operand')
        right, left = stack.pop(), stack.pop()
        if symbol == '+':
            value = left + right
        elif symbol == '-':
            value = left - right
        elif symbol == '*':
            value = left * right
        else:
            if right == 0:
                raise ZeroDivisionError('postfix division by zero')
            magnitude = abs(left) // abs(right)
            value = -magnitude if (left < 0) != (right < 0) else magnitude
        stack.append(value)
    if len(stack) != 1:
        raise ValueError('expected exactly one complete expression')
    return stack[0]
