"""Public username rules; mirrored by the immutable profile/auth guards in the database migration."""

import re
import unicodedata

MIN_USERNAME, MAX_USERNAME = 3, 24
_SHAPE = re.compile(r"[A-Za-zא-ת0-9_]{3,24}\Z")
_LETTER = re.compile(r"[A-Za-zא-ת]")
_LEET = str.maketrans("01345789", "oieastbg")
RESERVED = {"admin", "administrator", "moderator", "support", "system", "jobrun", "muxi", "מוקסי", "תמיכה", "מנהל"}
OFFENSIVE = {
    "fuck", "fucker", "fucking", "fuckyou", "fuckoff", "motherfucker", "fck", "fuk", "fcuk", "phuck",
    "shit", "bullshit", "asshole", "bastard", "bitch", "cunt", "dick", "cock", "pussy", "whore", "slut",
    "nigger", "nigga", "faggot", "fag", "retard", "nazi", "hitler", "heilhitler", "kkk",
    "זין", "כוס", "זונה", "שרמוטה", "מניאק", "בןזונה", "בתזונה", "בןשרמוטה", "כוסאמא", "כוסאמאשלך",
    "כוסאמק", "נאצי", "נאצים", "היטלר", "חרא", "לזיין", "מזדיין", "מזדיינת", "זיונים",
}
_OFFENSIVE_PATTERNS = tuple(re.compile("".join(re.escape(letter) + "+" for letter in word) + r"\Z")
                            for word in OFFENSIVE)
_CLEAR_STEMS = {"fuck", "faggot", "nigger", "nigga", "heilhitler", "שרמוט", "בןזונה", "בתזונה", "כוסאמא", "כוסאמק", "מזדיין", "מזדיינת", "לזיין"}
_STEM_PATTERNS = tuple(re.compile("".join(re.escape(letter) + "+" for letter in word)) for word in _CLEAR_STEMS)


def display_username(value: str) -> str:
    return unicodedata.normalize("NFKC", value.strip())


def username_key(value: str) -> str:
    return display_username(value).lower()


def username_reason(value: str) -> str | None:
    normalized = display_username(value)
    if not _SHAPE.fullmatch(normalized) or not _LETTER.search(normalized):
        return "invalid"
    key = normalized.lower()
    if key in RESERVED:
        return "invalid"
    # Whole tokens and an underscore-joined phrase catch f_u_c_k / בן_זונה without substring false positives
    # such as Scunthorpe, assistant, classroom, analyst or a surname containing a short banned word.
    for token in [*key.split("_"), key.replace("_", "")]:
        for candidate in (token, re.sub(r"^[0-9]+|[0-9]+$", "", token)):
            decoded = candidate.translate(_LEET)
            if (any(pattern.fullmatch(decoded) for pattern in _OFFENSIVE_PATTERNS) or
                    any(pattern.search(decoded) for pattern in _STEM_PATTERNS)):
                return "offensive"
    return None
