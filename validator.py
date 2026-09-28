import re
import warnings
from datetime import datetime, timedelta

import pandas as pd

import config
from formatter import clean_header, is_title_case_column, smart_title

EMAIL_REGEX = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")


# ---------------- Column type detection ----------------
def _tokens(header):
    h = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(header))          # camelCase -> camel Case
    toks = re.findall(r"[a-z]+|\d+", h.lower())
    pairs = [a + b for a, b in zip(toks, toks[1:])]
    return set(toks) | set(pairs) | {"".join(toks)}


def detect_type(header):
    t = _tokens(header)
    for kind, keys in (("email", config.EMAIL_KEYS), ("cnic", config.CNIC_KEYS),
                       ("phone", config.PHONE_KEYS), ("date", config.DATE_KEYS),
                       ("numeric", config.NUMERIC_KEYS)):
        if t & set(keys):
            return kind
    return "text"


# ---------------- Field cleaners: return (value, ok) ----------------
def clean_email(v):
    s = str(v).strip().lower().replace(" ", "")
    if s.startswith("mailto:"):
        s = s[7:]
    if "@" in s:
        user, _, domain = s.rpartition("@")
        s = f"{user}@{config.EMAIL_DOMAIN_FIXES.get(domain, domain)}"
    ok = bool(EMAIL_REGEX.match(s)) and ".." not in s
    return (s if ok else str(v).strip()), ok


def clean_phone(v):
    raw = str(v).strip()
    digits = re.sub(r"\D", "", raw)
    intl = raw.startswith("+")
    if digits.startswith("00"):
        digits, intl = digits[2:], True

    if config.DEFAULT_COUNTRY == "PK":
        if digits.startswith("92") and (intl or len(digits) == 12):
            national = "0" + digits[2:]
        elif intl:                                   # doosre mulk ka number (+44, +1 ...)
            ok = 8 <= len(digits) <= 15
            return ("+" + digits if ok else raw), ok
        elif len(digits) == 10 and digits.startswith("3"):
            national = "0" + digits
        else:
            national = digits
        ok = bool(re.fullmatch(r"03\d{9}", national) or re.fullmatch(r"0[1-9]\d{8,9}", national))
        if not ok:
            return raw, False
        return (national if config.PHONE_OUTPUT == "local" else "+92" + national[1:]), True

    # Baaqi mulk: E.164 jaisa (8-15 digits)
    ok = 7 <= len(digits) <= 15
    return (("+" + digits if intl else digits) if ok else raw), ok


def clean_cnic(v):
    digits = re.sub(r"\D", "", str(v))
    if len(digits) == 13:
        return f"{digits[:5]}-{digits[5:12]}-{digits[12]}", True
    return str(v).strip(), False


def clean_number(v):
    s = str(v).strip()
    negative = s.startswith("(") and s.endswith(")")
    s = re.sub(r"(?i)\b(rs|pkr|usd|eur|gbp|aed|sar)\b\.?|[$€£₨,\s()]", "", s)
    if s.startswith("-"):
        negative, s = True, s[1:]
    if not re.fullmatch(r"\d+(\.\d+)?|\.\d+", s):
        return str(v).strip(), False
    num = float(s) if "." in s else int(s)
    return (-num if negative else num), True


def clean_date(v):
    s = str(v).strip()
    try:
        if re.fullmatch(r"\d{5}(\.\d+)?", s) and 20000 <= float(s) <= 80000:   # Excel serial date
            d = datetime(1899, 12, 30) + timedelta(days=float(s))
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                iso = bool(re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}.*", s))
                d = pd.to_datetime(s, dayfirst=config.DATE_DAYFIRST and not iso, errors="coerce")
            if pd.isna(d):
                return s, False
        return d.strftime(config.DATE_OUTPUT_FORMAT), True
    except (ValueError, OverflowError):
        return s, False


def clean_text(v, title):
    s = re.sub(r"\s+", " ", str(v)).strip()
    if title and s:
        s = smart_title(s.lower()) if s.isupper() else smart_title(s)
    return s


CLEANERS = {"email": clean_email, "phone": clean_phone, "cnic": clean_cnic,
            "numeric": clean_number, "date": clean_date}


# ---------------- Pipeline ----------------
def process_validation(df):
    """Return (clean_df with Issues column, bad_cells DataFrame[bool], report dict)."""
    report = {"rows_in": len(df)}

    empty = df.apply(lambda r: all(str(v).strip() == "" for v in r), axis=1)
    df = df[~empty].copy()
    report["empty_rows_removed"] = int(empty.sum())

    headers, seen = [], {}
    for c in df.columns:
        h = clean_header(c) or "Column"
        seen[h.lower()] = seen.get(h.lower(), 0) + 1
        headers.append(h if seen[h.lower()] == 1 else f"{h}_{seen[h.lower()]}")
    df.columns = headers
    types = {c: detect_type(c) for c in df.columns}
    report["column_types"] = types

    bad = pd.DataFrame(False, index=df.index, columns=df.columns)
    counts = {k: {"invalid": 0, "missing": 0} for k in CLEANERS}

    for col, kind in types.items():
        new_vals = []
        for idx, v in df[col].items():
            if str(v).strip() == "":
                if kind in counts:
                    counts[kind]["missing"] += 1
                new_vals.append("" if kind != "text" else config.MISSING_TEXT)
                continue
            if kind == "text":
                new_vals.append(clean_text(v, is_title_case_column(col)))
                continue
            value, ok = CLEANERS[kind](v)
            if not ok:
                bad.at[idx, col] = True
                counts[kind]["invalid"] += 1
            new_vals.append(value)
        df[col] = new_vals

    if config.REMOVE_DUPLICATES:
        dup = df.astype(str).apply(lambda r: "|".join(x.lower() for x in r), axis=1).duplicated()
        report["duplicates_removed"] = int(dup.sum())
        df, bad = df[~dup], bad[~dup]
    else:
        report["duplicates_removed"] = 0

    df["Issues"] = [
        "; ".join(f"Invalid {c}" for c in bad.columns if bad.at[i, c]) or "OK" for i in df.index
    ]
    report["rows_out"] = len(df)
    report["rows_with_issues"] = int((df["Issues"] != "OK").sum())
    report["counts"] = counts
    return df.reset_index(drop=True), bad.reset_index(drop=True), report
