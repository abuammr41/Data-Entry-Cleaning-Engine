import csv
import io
import os
import re

import pandas as pd


def _read_text(path):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read file encoding: {path}")


def _read_csv(path, **kw):
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc, keep_default_na=False, **kw)
        except UnicodeDecodeError as exc:
            last = exc
    raise last


# ---------------- TXT support ----------------
KV_LINE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _./#()-]{0,40}?)\s*[:=]\s*(.*)$")


def _txt_as_table(text):
    """Comma / tab / | / ; wali table. Har line mein barabar columns hon to hi table maano."""
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return None
    sample = "\n".join(lines[:50])
    for delim in ("\t", "|", ";", ","):
        counts = [len(next(csv.reader([l], delimiter=delim))) for l in lines[:50]]
        if counts[0] >= 2 and sum(c == counts[0] for c in counts) >= 0.8 * len(counts):
            df = pd.read_csv(io.StringIO("\n".join(lines)), sep=delim, dtype=str,
                             keep_default_na=False, skipinitialspace=True, on_bad_lines="skip")
            df.columns = [str(c).strip() for c in df.columns]
            return df.apply(lambda col: col.str.strip())
    return None


def _txt_as_key_value(text):
    """
    'Name: Ali' / 'Email = x@y.com' jaisi lines. Records khali line se alag hon —
    ya pehla key dobara aaye to naya record shuru.
    """
    lines = text.splitlines()
    non_empty = [l for l in lines if l.strip()]
    if not non_empty or sum(bool(KV_LINE.match(l)) for l in non_empty) < 0.7 * len(non_empty):
        return None
    records, current, first_key = [], {}, None
    for line in lines:
        if not line.strip():
            if current:
                records.append(current)
                current = {}
            continue
        m = KV_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1).strip(), m.group(2).strip()
        first_key = first_key or key
        if key == first_key and current:
            records.append(current)
            current = {}
        current[key] = value
    if current:
        records.append(current)
    return pd.DataFrame(records).fillna("") if records else None


def _txt_as_free_lines(text):
    """Bikhra text: har line ek row + usme se email/phone/CNIC nikaal kar alag columns."""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s)
        cnic = re.search(r"\b\d{5}-?\d{7}-?\d\b", s)
        rest = s.replace(cnic.group(0), " ") if cnic else s
        phone = re.search(r"(?:\+\d{1,3}[\s-]?)?0?\d{2,4}[\s-]?\d{6,8}", rest)
        rows.append({"Text": s,
                     "Email": email.group(0) if email else "",
                     "Phone": phone.group(0) if phone else "",
                     "CNIC": cnic.group(0) if cnic else ""})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Text", "Email", "Phone", "CNIC"])


def read_txt(path):
    text = _read_text(path)
    for reader in (_txt_as_key_value, _txt_as_table):
        df = reader(text)
        if df is not None and len(df.columns) >= 2:
            return df
    return _txt_as_free_lines(text)


# ---------------- Main entry ----------------
def extract_raw_data(file_path):
    """Sab kuch TEXT ki tarah padho — taake ZIP/ID/CNIC ke aage wale zero na mitein."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = _read_csv(file_path)
    elif ext in (".xls", ".xlsx"):
        df = pd.read_excel(file_path, dtype=str, keep_default_na=False)
    elif ext == ".json":
        df = pd.read_json(file_path, dtype=False).astype(str).replace({"nan": "", "None": ""})
    elif ext == ".tsv":
        df = _read_csv(file_path, sep="\t")
    elif ext == ".txt":
        df = read_txt(file_path)
    else:
        df = _read_csv(file_path, sep=None, engine="python")

    df = df.fillna("")
    df.columns = [str(c).strip() for c in df.columns]
    return df
