"""
Data Entry Engine — settings. Client ki zaroorat ke hisaab se yahan badlo.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- Phones ----------
DEFAULT_COUNTRY = "PK"          # bina country code wale numbers is mulk ke maane jayenge
PHONE_OUTPUT = "local"          # "local" -> 03001234567 | "international" -> +923001234567

# ---------- Dates ----------
DATE_DAYFIRST = True            # 05/09/2026 = 5 Sep (Pakistan/UK). US client ke liye False
DATE_OUTPUT_FORMAT = "%Y-%m-%d" # jaise "%d-%m-%Y" ya "%m/%d/%Y"

# ---------- Cleaning ----------
REMOVE_DUPLICATES = True
MISSING_TEXT = "N/A"            # khali text cells mein kya likhna hai ("" = khali chhodo)

# ---------- Column detection (header ke alfaaz se) ----------
EMAIL_KEYS = ["email", "mail", "emailaddress"]
PHONE_KEYS = ["phone", "mobile", "cell", "whatsapp", "tel", "telephone", "contactno", "contactnumber", "mob"]
CNIC_KEYS = ["cnic", "nic", "nationalid", "idcard"]
DATE_KEYS = ["date", "dob", "birth", "joined", "joining", "createdat", "updatedat"]
NUMERIC_KEYS = ["price", "amount", "salary", "fee", "fees", "cost", "total", "balance",
                "payment", "rate", "quantity", "qty", "age", "income", "revenue"]
# Sirf in columns ka Title Case (naam jaisi cheezein). Codes, IDs, products waise hi rehte hain.
TITLE_CASE_KEYS = ["name", "city", "country", "province", "state", "district", "area",
                   "town", "fathername", "firstname", "lastname", "fullname"]

# Aam email spelling ghaltiyan — khud theek ho jati hain
EMAIL_DOMAIN_FIXES = {
    "gmial.com": "gmail.com", "gamil.com": "gmail.com", "gmai.com": "gmail.com",
    "gmail.co": "gmail.com", "gmail.con": "gmail.com", "gmail.cm": "gmail.com",
    "hotmial.com": "hotmail.com", "hotmail.con": "hotmail.com",
    "yahooo.com": "yahoo.com", "yaho.com": "yahoo.com", "yahoo.con": "yahoo.com",
    "outlok.com": "outlook.com", "outlook.con": "outlook.com",
}
