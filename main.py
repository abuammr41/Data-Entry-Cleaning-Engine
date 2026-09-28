import argparse
import os
import sys
import time

from exporter import export_formatted_excel
from extractor import extract_raw_data
from validator import process_validation


def run_data_entry_pipeline(file_path, output_name=None):
    start = time.time()
    df_raw = extract_raw_data(file_path)
    df_clean, bad, report = process_validation(df_raw)
    if output_name is None:
        output_name = f"Cleaned_{os.path.splitext(os.path.basename(file_path))[0]}.xlsx"
    output_path = export_formatted_excel(df_clean, bad, report, output_name)
    report["seconds"] = round(time.time() - start, 2)
    report["output"] = output_path
    return df_clean, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated data entry cleaning engine")
    parser.add_argument("input_file", nargs="?", default="raw_data_entry.csv", help="CSV / XLSX / XLS / JSON / TSV")
    parser.add_argument("-o", "--output", default=None, help="Output Excel file name (saved in output/)")
    args = parser.parse_args()

    try:
        _, rep = run_data_entry_pipeline(args.input_file, args.output)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print("==========================================")
    print("   AUTOMATED DATA ENTRY PIPELINE COMPLETED")
    print("==========================================")
    print(f"Rows received          : {rep['rows_in']}")
    print(f"Empty rows removed     : {rep['empty_rows_removed']}")
    print(f"Duplicate rows removed : {rep['duplicates_removed']}")
    print(f"Clean rows delivered   : {rep['rows_out']}")
    print(f"Rows needing review    : {rep['rows_with_issues']}")
    for kind, c in rep["counts"].items():
        if kind in rep["column_types"].values():
            print(f"{kind.capitalize():<22} : {c['invalid']} invalid, {c['missing']} missing")
    print(f"Time                   : {rep['seconds']} seconds")
    print(f"Excel saved at         : {rep['output']}")
