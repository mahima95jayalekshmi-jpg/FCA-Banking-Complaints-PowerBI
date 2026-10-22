"""Load FCA firm-level complaints files, build the SQLite star schema, run the
quality checks and analysis, and export the model for Power BI.

Usage (from the project folder):
    python etl/load_fca.py

Input:  every data/raw/firm-level-complaints-data-YYYY-hN.xlsx file
Output: results/uk_bank_complaints.db   SQLite database (not committed)
        results/*.csv                   quality checks and analysis results
        powerbi/data/*.csv              star-schema tables for Power BI
"""

import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
REFERENCE_FILE = PROJECT_DIR / "data" / "reference" / "banking_groups.csv"
SQL_DIR = PROJECT_DIR / "sql"
RESULTS_DIR = PROJECT_DIR / "results"
POWERBI_DIR = PROJECT_DIR / "powerbi" / "data"
DATABASE = RESULTS_DIR / "uk_bank_complaints.db"

FILE_PATTERN = re.compile(r"firm-level-complaints-data-(\d{4})-h([12])\.xlsx$", re.IGNORECASE)
ID_COLUMNS = ["Firm Name", "Group", "Joint Reporting", "Reporting period"]

# Sheet name -> staging column. Sheets are matched by prefix because Excel
# truncates sheet names to 31 characters ("Percentage after 3 days, within").
MEASURE_SHEETS = {
    "Opened": "opened",
    "Closed": "closed",
    "Percentage within 3 days": "pct_closed_3_days",
    "Percentage after 3 days": "pct_closed_8_weeks",
    "Percentage upheld": "pct_upheld",
}
PERCENT_COLUMNS = ["pct_closed_3_days", "pct_closed_8_weeks", "pct_upheld"]
CONTEXT_SHEETS = {"Context - Provision": "Provision", "Context - Intermediation": "Intermediation"}


# --------------------------------------------------------------------------- #
# Extract
# --------------------------------------------------------------------------- #
def find_sheet(sheets: dict, prefix: str) -> pd.DataFrame:
    for name, frame in sheets.items():
        if name.strip().lower().startswith(prefix.lower()):
            return frame
    raise KeyError(f"No sheet starting with '{prefix}'. Sheets found: {list(sheets)}")


def melt_products(frame: pd.DataFrame, value_name: str) -> pd.DataFrame:
    """Wide (one column per product) -> long (one row per firm and product)."""
    frame = frame.copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    product_columns = [c for c in frame.columns if c not in ID_COLUMNS and c != "Grand Total"]
    long = frame.melt(
        id_vars=[c for c in ID_COLUMNS if c in frame.columns],
        value_vars=product_columns,
        var_name="product_group",
        value_name=value_name,
    )
    return long.dropna(subset=[value_name])


def check_grand_totals(frame: pd.DataFrame, sheet: str, period: str) -> int:
    products = [c for c in frame.columns if c not in ID_COLUMNS and c != "Grand Total"]
    difference = frame[products].fillna(0).sum(axis=1) - frame["Grand Total"]
    mismatches = int((difference.abs() > 0.5).sum())
    if mismatches:
        print(f"  WARNING {period} {sheet}: {mismatches} firms where products do not sum to Grand Total")
    return mismatches


def read_file(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, list]:
    year, half = FILE_PATTERN.search(path.name).groups()
    period = f"{year} H{half}"
    sheets = pd.read_excel(path, sheet_name=None)
    checks = []

    # Main return: merge the five measure sheets on firm + product
    merged = None
    for prefix, column in MEASURE_SHEETS.items():
        sheet = find_sheet(sheets, prefix)
        sheet.columns = [str(c).strip() for c in sheet.columns]
        if column in ("opened", "closed"):
            checks.append((period, f"{prefix}: products != Grand Total", check_grand_totals(sheet, prefix, period)))
        long = melt_products(sheet, column)
        keep = ["Firm Name", "product_group", column]
        if merged is None:
            merged = long
        else:
            merged = merged.merge(long[keep], on=["Firm Name", "product_group"], how="outer")

    # Firm attributes come from the Opened sheet; fill them for any firm that
    # appears only in another sheet
    attributes = find_sheet(sheets, "Opened")[ID_COLUMNS].drop_duplicates("Firm Name")
    merged = merged.drop(columns=[c for c in ID_COLUMNS[1:] if c in merged.columns])
    merged = merged.merge(attributes, on="Firm Name", how="left")

    # Context: complaints per 1,000 accounts/policies. Provision first, then intermediation.
    context_parts = []
    for prefix, basis in CONTEXT_SHEETS.items():
        try:
            long = melt_products(find_sheet(sheets, prefix), "complaints_per_1000")
        except KeyError:
            continue
        context_parts.append(long[["Firm Name", "product_group", "complaints_per_1000"]].assign(context_basis=basis))
    if context_parts:
        context = pd.concat(context_parts).drop_duplicates(["Firm Name", "product_group"], keep="first")
        merged = merged.merge(context, on=["Firm Name", "product_group"], how="left")
    else:
        merged["complaints_per_1000"] = None
        merged["context_basis"] = None

    for column in PERCENT_COLUMNS:
        merged[column] = merged[column] * 100  # FCA publishes fractions (0.4135 = 41.35%)

    # Rows with no complaints in either direction carry no information
    merged = merged[(merged["opened"].fillna(0) > 0) | (merged["closed"].fillna(0) > 0)]

    main = pd.DataFrame(
        {
            "period_label": period,
            "firm_name": merged["Firm Name"].str.strip(),
            "fca_group": merged["Group"].str.strip(),
            "joint_reporting": merged["Joint Reporting"],
            "reporting_period": merged["Reporting period"],
            "product_group": merged["product_group"],
            "opened": merged["opened"],
            "closed": merged["closed"],
            "pct_closed_3_days": merged["pct_closed_3_days"],
            "pct_closed_8_weeks": merged["pct_closed_8_weeks"],
            "pct_upheld": merged["pct_upheld"],
            "complaints_per_1000": merged["complaints_per_1000"],
            "context_basis": merged["context_basis"],
            "source_file": path.name,
        }
    )

    # Consumer credit return
    try:
        cc = find_sheet(sheets, "Consumer Credit")
        cc.columns = [str(c).strip() for c in cc.columns]
        credit = pd.DataFrame(
            {
                "period_label": period,
                "firm_name": cc["Firm Name"].str.strip(),
                "fca_group": cc["Group"].str.strip(),
                "reporting_period": cc["Reporting period"],
                "received": cc["Complaints Received"],
                "closed": cc["Complaints Closed"],
                "pct_upheld": cc["Complaints upheld by firm"] * 100,
                "source_file": path.name,
            }
        )
    except KeyError:
        credit = pd.DataFrame()

    print(f"  {path.name}: {len(main):,} firm-product rows, {main['firm_name'].nunique()} firms, "
          f"{len(credit):,} consumer credit rows")
    return main, credit, checks


# --------------------------------------------------------------------------- #
# Load, model, check, analyse
# --------------------------------------------------------------------------- #
def run_script(conn: sqlite3.Connection, name: str):
    conn.executescript((SQL_DIR / name).read_text())


def split_queries(sql_text: str) -> list[tuple[str, str]]:
    """Split a .sql file into (title, query) pairs using the '-- N.' / '-- QN.' comments."""
    blocks, title, lines = [], None, []
    for line in sql_text.splitlines():
        heading = re.match(r"--\s*(Q?\d+)\.\s*(.*)", line)
        if heading:
            if title and "SELECT" in "\n".join(lines).upper():
                blocks.append((title, "\n".join(lines)))
            title, lines = f"{heading.group(1)}_{heading.group(2)}", []
        elif not line.strip().startswith("--"):
            lines.append(line)
    if title and "SELECT" in "\n".join(lines).upper():
        blocks.append((title, "\n".join(lines)))
    return blocks


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]


def main():
    files = sorted(p for p in RAW_DIR.glob("*.xlsx") if FILE_PATTERN.search(p.name))
    if not files:
        sys.exit(f"No FCA files found in {RAW_DIR}. Expected names like firm-level-complaints-data-2026-h1.xlsx")

    RESULTS_DIR.mkdir(exist_ok=True)
    POWERBI_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading {len(files)} file(s)")
    mains, credits, checks = [], [], []
    for path in files:
        main_rows, credit_rows, file_checks = read_file(path)
        mains.append(main_rows)
        credits.append(credit_rows)
        checks.extend(file_checks)
    staging = pd.concat(mains, ignore_index=True)
    credit = pd.concat(credits, ignore_index=True)

    DATABASE.unlink(missing_ok=True)
    with sqlite3.connect(DATABASE) as conn:
        run_script(conn, "01_schema.sql")
        staging.to_sql("stg_complaints", conn, if_exists="append", index=False)
        if not credit.empty:
            credit.to_sql("stg_consumer_credit", conn, if_exists="append", index=False)
        pd.read_csv(REFERENCE_FILE).to_sql("ref_banking_groups", conn, if_exists="append", index=False)
        run_script(conn, "02_build_model.sql")

        # Quality checks
        pd.DataFrame(checks, columns=["period", "check", "flagged"]).to_csv(
            RESULTS_DIR / "qc_grand_totals.csv", index=False)
        print("\nQuality checks")
        for title, query in split_queries((SQL_DIR / "03_quality_checks.sql").read_text()):
            result = pd.read_sql(query, conn)
            result.to_csv(RESULTS_DIR / f"qc_{slug(title)}.csv", index=False)
            print(f"  {title[:70]:<70} -> {len(result)} row(s)")

        # Analysis
        print("\nAnalysis")
        for title, query in split_queries((SQL_DIR / "04_analysis.sql").read_text()):
            result = pd.read_sql(query, conn)
            result.to_csv(RESULTS_DIR / f"{slug(title)}.csv", index=False)
            print(f"\n{title}\n{result.head(15).to_string(index=False)}")

        # Export star schema for Power BI
        for table in ["fact_complaints", "dim_firm", "dim_period", "dim_product"]:
            pd.read_sql(f"SELECT * FROM {table}", conn).to_csv(POWERBI_DIR / f"{table}.csv", index=False)
        if not credit.empty:
            pd.read_sql("SELECT * FROM stg_consumer_credit", conn).to_csv(
                POWERBI_DIR / "consumer_credit.csv", index=False)

    print(f"\nDone. Database: {DATABASE.relative_to(PROJECT_DIR)} | Power BI tables: "
          f"{POWERBI_DIR.relative_to(PROJECT_DIR)}/")


if __name__ == "__main__":
    main()
