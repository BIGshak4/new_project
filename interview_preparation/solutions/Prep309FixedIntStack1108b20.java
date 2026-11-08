import java.util.NoSuchElementException;

/** Fixed capacity, integer values, single-threaded ownership. */
public final class Prep309FixedIntStack1108b20 {
    private final int[] data;
    private int size;

    public Prep309FixedIntStack1108b20(int capacity) {
        if (capacity < 0) throw new IllegalArgumentException("negative capacity");
        data = new int[capacity];
        size = 0;
    }

    public void push(int value) {
        if (isFull()) throw new IllegalStateException("stack is full");
        data[size++] = value;
    }

    public int pop() {
        if (isEmpty()) throw new NoSuchElementException("stack is empty");
        return data[--size];
    }

    public boolean isEmpty() { return size == 0; }
    public boolean isFull() { return size == data.length; }

    public boolean exists(int value) {
        for (int i = 0; i < size; ++i) {
            if (data[i] == value) return true;
        }
        return false;
    }
}
