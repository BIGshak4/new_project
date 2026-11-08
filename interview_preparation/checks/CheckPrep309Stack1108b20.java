import java.util.ArrayDeque;
import java.util.NoSuchElementException;
import java.util.Random;

public final class CheckPrep309Stack1108b20 {
    private static void require(boolean condition) {
        if (!condition) throw new AssertionError();
    }

    public static void main(String[] args) {
        try {
            new Prep309FixedIntStack1108b20(-1);
            throw new AssertionError("negative capacity accepted");
        } catch (IllegalArgumentException expected) { }
        int checks = 1;
        for (int capacity : new int[]{0, 1, 7}) {
            Prep309FixedIntStack1108b20 actual = new Prep309FixedIntStack1108b20(capacity);
            ArrayDeque<Integer> model = new ArrayDeque<>();
            Random random = new Random(309 + capacity);
            for (int step = 0; step < 4000; ++step) {
                int operation = random.nextInt(3);
                int value = random.nextInt(11) - 5;
                if (operation == 0) {
                    if (model.size() == capacity) {
                        try { actual.push(value); throw new AssertionError("full push accepted"); }
                        catch (IllegalStateException expected) { }
                    } else {
                        actual.push(value); model.push(value);
                    }
                } else if (operation == 1) {
                    if (model.isEmpty()) {
                        try { actual.pop(); throw new AssertionError("empty pop accepted"); }
                        catch (NoSuchElementException expected) { }
                    } else require(actual.pop() == model.pop());
                } else require(actual.exists(value) == model.contains(value));
                require(actual.isEmpty() == model.isEmpty());
                require(actual.isFull() == (model.size() == capacity));
                ++checks;
            }
        }
        Prep309FixedIntStack1108b20 stack = new Prep309FixedIntStack1108b20(2);
        stack.push(7); stack.push(7);
        require(stack.pop() == 7 && stack.exists(7));
        require(stack.pop() == 7 && !stack.exists(7));
        checks += 2;
        System.out.println("PREP-309 Java: " + checks + " checks passed");
    }
}
