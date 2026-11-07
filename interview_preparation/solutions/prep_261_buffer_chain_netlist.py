"""Report one longest buffer-only witness per endpoint in a directed netlist.

Input: nodes[name] is a kind: buffer, logic, ff or port.
edges[name] lists (target, pin_role); pin_role is wire for a buffer target,
otherwise data/reset/clock from trusted cell-library/interface metadata.
No graph-name/fanout heuristic is used to declare a reset. Buffer cycles are
rejected. Control-only cones may be excluded; mixed-use cones are retained.
"""
from collections import deque


def buffer_chains(nodes, edges, limit=10, exclude_control=True):
    if type(limit) is not int or limit < 0:
        raise ValueError('Nonnegative integer limit required')
    if any(kind not in {'buffer', 'logic', 'ff', 'port'} for kind in nodes.values()):
        raise ValueError('Unknown cell kind')
    if set(edges) - set(nodes):
        raise ValueError('Unknown source cell')
    buffers = {name for name, kind in nodes.items() if kind == 'buffer'}
    succ = {name: [] for name in buffers}
    terminal_roles = {name: set() for name in buffers}
    incoming = {name: 0 for name in buffers}
    for source in nodes:
        seen = set()
        for target, role in edges.get(source, []):
            if target not in nodes or (target, role) in seen:
                raise ValueError('Unknown target or duplicate edge')
            seen.add((target, role))
            if role not in {'wire', 'data', 'reset', 'clock'}:
                raise ValueError('Unknown pin role')
            if source not in buffers:
                continue
            if target in buffers:
                if role != 'wire':
                    raise ValueError('Buffer-to-buffer connections use wire role')
                succ[source].append(target)
                incoming[target] += 1
            else:
                if role == 'wire':
                    raise ValueError('Nonbuffer target requires a terminal pin role')
                terminal_roles[source].add(role)
    ready = deque(sorted(name for name in buffers if not incoming[name]))
    order = []
    while ready:
        source = ready.popleft()
        order.append(source)
        for target in sorted(succ[source]):
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    if len(order) != len(buffers):
        raise ValueError('Buffer-only cycle: a DAG contract is required')
    roles = {name: set(terminal_roles[name]) for name in buffers}
    for source in reversed(order):
        for target in succ[source]:
            roles[source].update(roles[target])
    excluded = {name for name in buffers
                if exclude_control and roles[name]
                and roles[name] <= {'reset', 'clock'}}
    kept = buffers - excluded
    length = {name: 1 for name in kept}
    predecessor = {name: None for name in kept}
    for source in order:
        if source not in kept:
            continue
        for target in sorted(succ[source]):
            if target in kept and length[source] + 1 > length[target]:
                length[target] = length[source] + 1
                predecessor[target] = source
    reports = []
    for end in sorted(kept):
        if any(target in kept for target in succ[end]) or length[end] <= limit:
            continue
        path, current = [], end
        while current is not None:
            path.append(current)
            current = predecessor[current]
        reports.append({'end': end, 'length': length[end], 'witness': path[::-1]})
    return {'reports': reports, 'excluded_control_buffers': sorted(excluded),
            'longest_to_buffer': dict(sorted(length.items()))}
