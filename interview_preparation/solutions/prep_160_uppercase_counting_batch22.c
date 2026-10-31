/* C99 on an ASCII execution-character-set target. Validate before mutation. */
#include <stdbool.h>
#include <stddef.h>
bool sort_uppercase(char *letters, size_t length) {
    size_t counts[26] = {0};
    if (length != 0 && letters == NULL) return false;
    for (size_t i = 0; i < length; ++i) {
        unsigned char c = (unsigned char)letters[i];
        if (c < 'A' || c > 'Z') return false;
        ++counts[c - 'A'];
    }
    size_t write = 0;
    for (size_t letter = 0; letter < 26; ++letter)
        for (size_t n = 0; n < counts[letter]; ++n)
            letters[write++] = (char)('A' + letter);
    return true;
}
