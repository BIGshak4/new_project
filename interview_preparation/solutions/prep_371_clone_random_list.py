class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.random = None


def clone_list(head):
    copies = {None: None}
    node = head
    while node is not None:
        copies[node] = Node(node.data)
        node = node.next
    node = head
    while node is not None:
        copies[node].next = copies[node.next]
        copies[node].random = copies[node.random]
        node = node.next
    return copies[head]
