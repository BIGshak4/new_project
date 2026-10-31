"""Stack ADT trace; this does not model a particular machine ABI or CPU stack."""


def stack_trace(operations):
    items, removed = [], []
    for action, value in operations:
        if action == 'push':
            items.append(value)
        elif action == 'pop':
            if not items:
                raise IndexError('empty stack')
            removed.append(items.pop())
        else:
            raise ValueError('unknown operation')
    return {'removed': removed, 'remaining_bottom_to_top': items}
