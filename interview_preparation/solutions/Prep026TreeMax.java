import java.util.ArrayDeque;
import java.util.Deque;
import java.util.OptionalInt;

public final class Prep026TreeMax {
    static final class Node {
        final int value;
        Node left;
        Node right;
        Node(int value) { this.value = value; }
    }

    public static OptionalInt maximum(Node root) {
        if (root == null) return OptionalInt.empty();
        int best = root.value;
        Deque<Node> pending = new ArrayDeque<>();
        pending.push(root);
        while (!pending.isEmpty()) {
            Node node = pending.pop();
            best = Math.max(best, node.value);
            if (node.right != null) pending.push(node.right);
            if (node.left != null) pending.push(node.left);
        }
        return OptionalInt.of(best);
    }
}
