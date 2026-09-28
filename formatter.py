import re
import config


def _key(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def clean_header(name):
    """'first name ' -> 'First_Name', 'E-mail' -> 'E_Mail'"""
    parts = re.split(r"[\s_\-]+", str(name).strip())
    return "_".join(p[:1].upper() + p[1:] for p in parts if p)


def smart_title(text):
    """
    Naam jaisi cheezon ka Title Case — 'iPhone', 'McDonald', 'ABC' jaise alfaaz
    ko nahi chhedta. (Poori value BARE huroof mein ho, jaise 'ALI KHAN', to
    validator pehle usko chhota karta hai, phir -> 'Ali Khan'.)
    """
    words = []
    for w in text.split(" "):
        if w.islower():   # BARE HURUF wale alfaaz (ABC, USA, LLC) acronym maane jate hain — waise hi
            w = "-".join(p[:1].upper() + p[1:].lower() for p in w.split("-"))
        words.append(w)
    return " ".join(words)


def is_title_case_column(col):
    k = _key(col)
    return any(key in k for key in config.TITLE_CASE_KEYS)
