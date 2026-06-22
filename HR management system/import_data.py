"""
import_data.py

Reads CSV files and upserts records into the MySQL database named by MYSQL_DATABASE (default: hr_management).
Uses pandas and mysql-connector-python.

Usage:
    python import_data.py --dir /path/to/csvs --database hr_management

Environment variables (optional):
    MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

This script performs safe ETL with comprehensive foreign key validation, date conversion, and field cleaning.
"""

from pathlib import Path
import os
import sys
import argparse
import pandas as pd
import re
from mysql.connector import Error
from database import get_db_connection

PROCESS_ORDER = [
    "Departments",
    "Job_Postings",
    "Candidates",
    "Employees",
    "Trainers",
    "Applications",
    "Interviews",
    "Training_Programs",
    "Employee_Training",
]

TABLE_MAP = {
    "Departments": ("departments", ["Department_ID"]),
    "Job_Postings": ("job_postings", ["Job_ID"]),
    "Candidates": ("candidates", ["Candidate_ID"]),
    "Employees": ("employees", ["Employee_ID"]),
    "Trainers": ("trainers", ["Trainer_ID"]),
    "Applications": ("applications", ["Application_ID"]),
    "Interviews": ("interviews", ["Interview_ID"]),
    "Training_Programs": ("training_programs", ["Program_ID"]),
    "Employee_Training": ("employee_training", ["ET_ID"]),
}

PARENT_TABLES = {
    "job_postings": ["departments"],
    "applications": ["job_postings", "candidates"],
    "interviews": ["applications"],
    "employees": ["departments"],
    "employee_training": ["employees", "training_programs"],
}

FK_COLUMNS = {
    "job_postings": {"Department_ID": "departments.Department_ID"},
    "applications": {
        "Job_ID": "job_postings.Job_ID",
        "Candidate_ID": "candidates.Candidate_ID",
    },
    "interviews": {
        "application_id": "applications.Application_ID",
    },
    "employees": {"Department_ID": "departments.Department_ID"},
    "employee_training": {
        "Employee_ID": "employees.Employee_ID",
        "Program_ID": "training_programs.Program_ID",
    },
}


def read_csv(path):
    """Read CSV safely with BOM and whitespace cleanup."""
    if not path.exists():
        print(f"[SKIP] {path.name}: file not found")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False)
        df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
        print(f"[READ] {path.name}: {len(df)} rows")
        return df
    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return pd.DataFrame()


def get_table_columns(conn, table):
    """Get table schema from database."""
    cur = conn.cursor()
    try:
        cur.execute(f"DESCRIBE `{table}`")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()


def get_fk_values(conn, fk_table, fk_column):
    """Get all valid foreign key values from a table."""
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT DISTINCT `{fk_column}` FROM `{fk_table}`")
        values = {row[0] for row in cur.fetchall() if row[0]}
        return values
    except Exception as e:
        print(f"[FK_LOAD_ERROR] {fk_table}.{fk_column}: {e}")
        return set()
    finally:
        cur.close()


def safe_date(value):
    """Convert date string to YYYY-MM-DD or NULL. Supports DD/MM/YYYY format."""
    if not value or not str(value).strip():
        return None
    try:
        val = str(value).strip()
        parsed = pd.to_datetime(val, errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            return None
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return None


def clean_phone(value):
    """Clean phone/WhatsApp number: remove non-numeric, limit to 20 chars."""
    if not value or not str(value).strip():
        return None
    try:
        val = str(value).strip()
        cleaned = re.sub(r"\D", "", val)
        if not cleaned:
            return None
        return cleaned[:20]
    except Exception:
        return None


def normalize_df(df, table):
    """Normalize dataframe: dates, phones, IDs, NULLs."""
    df = df.copy()

    # Convert empty strings and whitespace-only strings to NULL
    df = df.replace(r"^\s*$", None, regex=True)

    # Clean ID columns (preserve case, strip spaces)
    for col in df.columns:
        if "id" in col.lower() and df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
            df.loc[df[col] == "", col] = None
            df.loc[df[col].str.lower() == "nan", col] = None

    # Convert date columns
    for col in df.columns:
        if "date" in col.lower():
            df[col] = df[col].apply(safe_date)

    # Clean phone/WhatsApp columns
    for col in df.columns:
        if "phone" in col.lower() or "whatsapp" in col.lower():
            df[col] = df[col].apply(clean_phone)

    # Clean other text fields (strip whitespace, replace empty with NULL)
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
            df.loc[df[col] == "", col] = None

    return df


def map_to_schema(df, schema_cols):
    """Map DataFrame columns to table schema by name (case-insensitive)."""
    if df.empty:
        return pd.DataFrame()

    schema_lower = {c.lower(): c for c in schema_cols}
    mapped_cols = {}

    for csv_col in df.columns:
        schema_col = schema_lower.get(csv_col.lower())
        if schema_col:
            mapped_cols[schema_col] = df[csv_col]

    if not mapped_cols:
        return pd.DataFrame()

    return pd.DataFrame(mapped_cols)


def validate_fks(conn, table, df, fk_map):
    """Filter rows with invalid foreign keys. Return cleaned df and count of filtered rows."""
    if not fk_map or df.empty:
        return df, 0

    filtered_count = 0
    for fk_col, fk_ref in fk_map.items():
        if fk_col not in df.columns:
            continue

        fk_table, fk_target = fk_ref.split(".")

        # Load valid FK values
        valid_fks = get_fk_values(conn, fk_table, fk_target)

        if not valid_fks:
            print(f"[FK_LOAD_WARN] {table}.{fk_col}: could not load valid FKs from {fk_ref}")
            continue

        # Filter rows with valid FKs
        before = len(df)
        df = df[df[fk_col].notna()]
        df = df[df[fk_col].astype(str).str.strip() != ""]
        df = df[df[fk_col].isin(valid_fks)]
        dropped = before - len(df)
        if dropped > 0:
            print(f"[FK_FILTER] {table}.{fk_col}: dropped {dropped} rows with invalid FK")
            filtered_count += dropped

    return df, filtered_count


def process_table(conn, csv_dir, csv_name, table, pk_cols):
    """Process a single CSV file and insert into table."""
    file_path = csv_dir / f"{csv_name}.csv"
    print(f"\n[PROCESS] {csv_name} -> {table}")

    # Read CSV
    df = read_csv(file_path)
    if df.empty:
        return 0

    rows_read = len(df)

    # Get schema
    schema_cols = get_table_columns(conn, table)
    if not schema_cols:
        print(f"[ERROR] {table}: could not load schema")
        return 0

    # Map columns to schema
    df = map_to_schema(df, schema_cols)
    if df.empty:
        print(f"[SKIP] {csv_name}: no columns mapped to schema")
        return 0

    # DEBUG: Show raw data for Candidates table
    if csv_name == "Candidates":
        pk_col = pk_cols[0]
        print(f"[DEBUG] {csv_name} columns: {list(df.columns)}")
        if pk_col in df.columns:
            print(f"[DEBUG] {csv_name} first 5 {pk_col} values:")
            for i, val in enumerate(df[pk_col].head()):
                print(f"  [{i}] repr={repr(val)}, stripped={repr(str(val).strip())}")

    # Normalize dates, phones, IDs, etc.
    df = normalize_df(df, table)

    # Check primary key
    pk_col = pk_cols[0]
    if pk_col not in df.columns:
        print(f"[ERROR] {csv_name}: PK column {pk_col} missing after schema mapping")
        return 0

    # Remove rows with NULL or empty PK
    before_pk = len(df)
    df = df[df[pk_col].notna()]
    df = df[df[pk_col].astype(str).str.strip() != ""]
    dropped_pk = before_pk - len(df)
    if dropped_pk > 0:
        print(f"[PK_FILTER] {table}: dropped {dropped_pk} rows with NULL/empty PK")

    if df.empty:
        print(f"[SKIP] {csv_name}: no rows with valid PK")
        return 0

    # Validate foreign keys
    fk_map = FK_COLUMNS.get(table, {})
    df, fk_dropped = validate_fks(conn, table, df, fk_map)

    if df.empty:
        print(f"[SKIP] {csv_name}: all rows dropped due to FK validation")
        return 0

    rows_after_clean = len(df)
    print(f"[CLEAN] {csv_name}: {rows_read} read -> {rows_after_clean} after cleaning")

    # Insert into database with IGNORE for duplicate keys
    cols = list(df.columns)
    placeholders = ",".join(["%s"] * len(cols))
    col_str = ",".join([f"`{c}`" for c in cols])
    sql = f"INSERT IGNORE INTO `{table}` ({col_str}) VALUES ({placeholders})"

    values = [tuple(None if pd.isna(x) else x for x in row) for row in df.to_numpy()]

    cur = conn.cursor()
    try:
        cur.executemany(sql, values)
        conn.commit()
        inserted = len(values)
        print(f"[INSERT] {table}: {inserted} rows inserted")
        return inserted
    except Error as e:
        print(f"[DB_ERROR] {table}: {e}")
        conn.rollback()
        return 0
    finally:
        cur.close()


def main(csv_dir, database=None):
    """Main ETL process."""
    if database:
        os.environ["MYSQL_DATABASE"] = database

    csv_path = Path(csv_dir)
    if not csv_path.exists():
        print(f"[ERROR] CSV directory not found: {csv_dir}")
        sys.exit(1)

    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        sys.exit(1)

    total_inserted = 0

    for csv_name in PROCESS_ORDER:
        if csv_name not in TABLE_MAP:
            continue

        table, pk_cols = TABLE_MAP[csv_name]

        try:
            inserted = process_table(conn, csv_path, csv_name, table, pk_cols)
            total_inserted += inserted
        except Exception as e:
            print(f"[ERROR] {csv_name}: {e}")
            continue

    try:
        conn.close()
    except Exception:
        pass

    print(f"\n[DONE] Total rows inserted: {total_inserted}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import CSVs into hr_management DB")
    parser.add_argument("--dir", "-d", default=".", help="Directory with CSV files")
    parser.add_argument(
        "--database", "-D", help="Override MYSQL_DATABASE env var"
    )
    args = parser.parse_args()

    main(args.dir, args.database)