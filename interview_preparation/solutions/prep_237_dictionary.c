/* C99 list-backed dictionary, not a hash table or full Python dict clone. */
#include "prep_237_dictionary.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct Entry {
    char *key, *value;
    struct Entry *next;
} Entry;
struct Dict { Entry *head; size_t count; };

static char *copy_text(const char *text) {
    size_t length = strlen(text);
    if (length == SIZE_MAX) return NULL;
    char *copy = malloc(length + 1);
    if (copy) memcpy(copy, text, length + 1);
    return copy;
}

Dict *dict_create(void) {
    Dict *dict = malloc(sizeof *dict);
    if (dict) { dict->head = NULL; dict->count = 0; }
    return dict;
}

DictStatus dict_put(Dict *dict, const char *key, const char *value) {
    if (!dict || !key || !value) return DICT_INVALID;
    for (Entry *entry = dict->head; entry; entry = entry->next) {
        if (strcmp(entry->key, key) == 0) {
            char *replacement = copy_text(value);
            if (!replacement) return DICT_OOM;
            free(entry->value);
            entry->value = replacement;
            return DICT_OK;
        }
    }
    if (dict->count == SIZE_MAX) return DICT_OOM;
    Entry *entry = malloc(sizeof *entry);
    if (!entry) return DICT_OOM;
    entry->key = copy_text(key);
    if (!entry->key) { free(entry); return DICT_OOM; }
    entry->value = copy_text(value);
    if (!entry->value) { free(entry->key); free(entry); return DICT_OOM; }
    entry->next = dict->head;
    dict->head = entry;
    ++dict->count;
    return DICT_OK;
}

const char *dict_get(const Dict *dict, const char *key) {
    if (!dict || !key) return NULL;
    for (const Entry *entry = dict->head; entry; entry = entry->next)
        if (strcmp(entry->key, key) == 0) return entry->value;
    return NULL;
}

DictStatus dict_remove(Dict *dict, const char *key) {
    if (!dict || !key) return DICT_INVALID;
    Entry **link = &dict->head;
    while (*link && strcmp((*link)->key, key) != 0) link = &(*link)->next;
    if (!*link) return DICT_NOT_FOUND;
    Entry *removed = *link;
    *link = removed->next;
    free(removed->key); free(removed->value); free(removed);
    --dict->count;
    return DICT_OK;
}

size_t dict_size(const Dict *dict) { return dict ? dict->count : 0; }

void dict_destroy(Dict *dict) {
    if (!dict) return;
    Entry *entry = dict->head;
    while (entry) {
        Entry *next = entry->next;
        free(entry->key); free(entry->value); free(entry);
        entry = next;
    }
    free(dict);
}
