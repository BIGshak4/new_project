// C++17. General binary tree: no BST ordering is assumed.
#include <optional>
#include <vector>

struct Node {
    int value;
    const Node* left = nullptr;
    const Node* right = nullptr;
};

std::optional<int> maximum(const Node* root) {
    if (root == nullptr) return std::nullopt;
    int best = root->value;
    std::vector<const Node*> pending{root};
    while (!pending.empty()) {
        const Node* node = pending.back();
        pending.pop_back();
        if (node->value > best) best = node->value;
        if (node->right) pending.push_back(node->right);
        if (node->left) pending.push_back(node->left);
    }
    return best;
}
