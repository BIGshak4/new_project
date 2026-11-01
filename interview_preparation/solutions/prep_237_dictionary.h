#ifndef PREP_237_DICTIONARY_H
#define PREP_237_DICTIONARY_H
#include <stddef.h>
typedef struct Dict Dict;
typedef enum { DICT_OK, DICT_OOM, DICT_INVALID, DICT_NOT_FOUND } DictStatus;
/* Live NUL-terminated keys/values; dictionary owns independent copies. */
Dict *dict_create(void);
DictStatus dict_put(Dict *dict, const char *key, const char *value);
/* Borrowed value: valid until that key is updated/removed or map destroyed. */
const char *dict_get(const Dict *dict, const char *key);
DictStatus dict_remove(Dict *dict, const char *key);
size_t dict_size(const Dict *dict);
void dict_destroy(Dict *dict); /* NULL is harmless. */
#endif
