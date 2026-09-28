# Data Entry Engine v2

Turns messy client data (CSV / Excel / JSON / TSV) into a clean, validated, formatted Excel file.
20,000 rows in about 25 seconds.

## Quick Start (Windows)

```
py -m pip install -r requirements.txt
py test_engine.py
py main.py raw_data_entry.csv
py main.py client_file.xlsx -o Client_Clean.xlsx
```
Output is saved in the `output/` folder.

## What it does

| Column type (detected from header) | Cleaning |
|---|---|
| Email (`Email`, `E-mail`, `Email Address`) | lowercase, trims, fixes typos (`gmial.com` → `gmail.com`), validates |
| Phone (`Phone`, `Mobile No`, `Cell`, `WhatsApp`) | Pakistan mobile + landline → `03001234567`; international kept as `+447911123456` |
| CNIC | 13 digits → `35202-1234567-1` |
| Numbers (`Amount`, `Price`, `Salary`, `Fee`, `Total`, `Qty`, `Age`...) | removes Rs/PKR/$/commas, keeps minus and `(1,250)` accounting negatives |
| Dates (`Date`, `DOB`, `Joining Date`) | any format + Excel serial numbers → `YYYY-MM-DD` |
| Names / City / Country | Smart Title Case (`ali khan` → `Ali Khan`, keeps `iPhone`, `ABC`) |
| Other text | extra spaces removed, left as written (codes, IDs, products not changed) |

Also: leading zeros kept (`00123`), empty rows removed, duplicate rows removed (after cleaning),
Excel/UTF-8 encodings supported.

## Output Excel

- **Summary** — rows in/out, empty & duplicate rows removed, invalid/missing per field
- **Clean_Data** — all rows; invalid cells highlighted red; `Issues` column per row
- **Needs_Review** — only rows that need a human check

## Settings (`config.py`)

`DEFAULT_COUNTRY`, `PHONE_OUTPUT` (local / international), `DATE_DAYFIRST` (False for US clients),
`DATE_OUTPUT_FORMAT`, `REMOVE_DUPLICATES`, `MISSING_TEXT`, and the header keyword lists.

## License

All Rights Reserved — shared publicly for portfolio/demonstration purposes only.
See [LICENSE](LICENSE). No reuse, copying, or redistribution without permission.
