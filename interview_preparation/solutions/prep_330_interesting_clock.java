class Solution {
    private int seconds(String time) {
        String[] fields = time.split(":");
        return Integer.parseInt(fields[0]) * 3600
            + Integer.parseInt(fields[1]) * 60 + Integer.parseInt(fields[2]);
    }

    public int solution(String S, String T) {
        int total = 0;
        for (int second = seconds(S); second <= seconds(T); ++second) {
            int hours = second / 3600;
            int minutes = (second / 60) % 60;
            int remaining = second % 60;
            int[] digits = {hours / 10, hours % 10, minutes / 10,
                            minutes % 10, remaining / 10, remaining % 10};
            int mask = 0;
            for (int digit : digits) mask |= 1 << digit;
            if (Integer.bitCount(mask) <= 2) ++total;
        }
        return total;
    }
}
