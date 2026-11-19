#include <stdio.h>

void print_binary(int value) {
    unsigned int magnitude = (unsigned int)value;
    if (value < 0) {
        putchar('-');
        magnitude = 0u - magnitude;
    }
    unsigned int mask = 1u;
    while (mask <= magnitude / 2u) {
        mask <<= 1;
    }
    do {
        putchar((magnitude & mask) ? '1' : '0');
        mask >>= 1;
    } while (mask != 0u);
}
