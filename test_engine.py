"""Tests — chalane ke 2 tareeqe:  py test_engine.py   ya   py -m pytest -q test_engine.py"""
import os
import openpyxl
import pandas as pd

import config
from formatter import smart_title
from main import run_data_entry_pipeline
from validator import (clean_cnic, clean_date, clean_email, clean_number, clean_phone,
                       detect_type, process_validation)

HERE = os.path.dirname(os.path.abspath(__file__))


def test_column_detection():
    assert detect_type("E-mail") == "email" and detect_type("Email Address") == "email"
    assert detect_type("Mobile No") == "phone" and detect_type("WhatsApp") == "phone"
    assert detect_type("Contact Person") == "text"          # naam hai, phone nahi
    assert detect_type("Feedback") == "text"                 # 'fee' nahi
    assert detect_type("Candidate Name") == "text"           # 'date' nahi
    assert detect_type("DateOfBirth") == "date" and detect_type("Total Amount") == "numeric"
    assert detect_type("CNIC") == "cnic"


def test_email():
    assert clean_email("ALI@GMIAL.COM") == ("ali@gmail.com", True)
    assert clean_email("mailto:x@y.com") == ("x@y.com", True)
    assert clean_email("sara@@mail")[1] is False and clean_email("a..b@x.com")[1] is False


def test_phone_pk_and_international():
    for raw in ("0300-1234567", "+92 300 1234567", "923001234567", "3001234567", "0092 300 1234567"):
        assert clean_phone(raw) == ("03001234567", True), raw
    assert clean_phone("042-35761234") == ("04235761234", True)       # landline
    assert clean_phone("+44 7911 123456") == ("+447911123456", True)  # UK
    assert clean_phone("12345")[1] is False


def test_cnic_number_date():
    assert clean_cnic("3520212345671") == ("35202-1234567-1", True)
    assert clean_cnic("12345")[1] is False
    assert clean_number("Rs. 1,500") == (1500, True)
    assert clean_number("(1,250.75)") == (-1250.75, True) and clean_number("-500") == (-500, True)
    assert clean_number("abc")[1] is False
    assert clean_date("05/09/2026") == ("2026-09-05", True)           # day-first
    assert clean_date("2026-09-05") == ("2026-09-05", True)
    assert clean_date("45905") == ("2025-09-05", True)                # Excel serial
    assert clean_date("31/02/2026")[1] is False


def test_title_case_is_smart():
    assert smart_title("ali khan") == "Ali Khan"
    assert smart_title("iPhone 15 pro") == "iPhone 15 Pro"
    assert smart_title("ABC traders") == "ABC Traders"


def test_full_pipeline():
    df, rep = run_data_entry_pipeline(os.path.join(HERE, "raw_data_entry.csv"), "test_output.xlsx")
    assert rep["empty_rows_removed"] == 1 and rep["duplicates_removed"] == 1 and rep["rows_out"] == 4
    ali = df.iloc[0]
    assert ali["Full_Name"] == "Ali Khan" and ali["E_Mail"] == "ali.khan@gmail.com"
    assert ali["Mobile_No"] == "03001234567" and ali["Zip_Code"] == "00123"
    assert ali["Product"] == "iPhone 15 Pro" and ali["Contact_Person"] == "Sara Ahmed"
    assert ali["Feedback"] == "Great service" and ali["Amount"] == 1500
    sara = df[df["E_Mail"] == "sara@@mail"].iloc[0]
    assert "Invalid E_Mail" in sara["Issues"] and "Invalid Amount" in sara["Issues"]
    wb = openpyxl.load_workbook(rep["output"])
    assert wb.sheetnames == ["Summary", "Clean_Data", "Needs_Review"]
    os.remove(rep["output"])


def test_leading_zeros_and_empty_input():
    df, _, rep = process_validation(pd.DataFrame({"ID": ["00012", "00012"], "Name": ["a", "b"]}))
    assert list(df["ID"]) == ["00012", "00012"]
    df, _, rep = process_validation(pd.DataFrame({"Name": ["", ""]}))
    assert rep["rows_out"] == 0


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\nALL {len(tests)} TESTS PASSED")
