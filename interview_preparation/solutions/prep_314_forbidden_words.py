def contains_no_forbidden_words(text, forbidden):
    """Compare complete, case-sensitive tokens separated by whitespace."""
    vocabulary = set(forbidden)
    return all(word not in vocabulary for word in text.split())
