#include <memory>
#include <unordered_map>
#include <vector>

struct Node {
    int data;
    Node* next = nullptr;
    Node* random = nullptr;
};

struct ClonedList {
    std::vector<std::unique_ptr<Node>> storage;
    Node* head = nullptr;
};

// The next chain is finite and acyclic. All non-null random targets lie in it.
ClonedList clone_list(const Node* head) {
    ClonedList result;
    std::unordered_map<const Node*, Node*> copies;
    copies.emplace(nullptr, nullptr);
    for (const Node* node = head; node; node = node->next) {
        result.storage.push_back(std::make_unique<Node>(Node{node->data}));
        copies.emplace(node, result.storage.back().get());
    }
    for (const Node* node = head; node; node = node->next) {
        Node* copy = copies.at(node);
        copy->next = copies.at(node->next);
        copy->random = copies.at(node->random);
    }
    result.head = copies.at(head);
    return result;
}
