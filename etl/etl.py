import hashlib
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOAD_DATE = datetime.now()
ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/EXR/"
    "D.USD+GBP+JPY+CHF.EUR.SP00.A"
    "?startPeriod=2025-10-01&endPeriod=2026-10-14&format=csvdata"
)


# ---------- 1. EXTRACT ----------

def extract_csv():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    payments = pd.read_csv(DATA_DIR / "payments.csv", parse_dates=["payment_date"])
    return customers, payments


def extract_ecb_rates():
    rates = pd.read_csv(ECB_URL)
    rates = rates[["TIME_PERIOD", "CURRENCY", "OBS_VALUE"]]
    rates.columns = ["rate_date", "currency", "exchange_rate"]
    rates["rate_date"] = pd.to_datetime(rates["rate_date"])
    return rates


# ---------- 2. VALIDATE ----------

def validate(payments, customers):
    payments = payments.copy()
    payments["error_reason"] = None

    duplicated = payments.duplicated(subset="payment_id", keep="first")
    payments.loc[duplicated, "error_reason"] = "duplicate payment_id"
    payments.loc[payments["amount"] <= 0, "error_reason"] = "amount not positive"
    payments.loc[payments["currency"].isna(), "error_reason"] = "missing currency"
    unknown = ~payments["customer_id"].isin(customers["customer_id"])
    payments.loc[unknown, "error_reason"] = "unknown customer_id"

    good = payments[payments["error_reason"].isna()].drop(columns="error_reason")
    bad = payments[payments["error_reason"].notna()]
    return good, bad


# ---------- 3. TRANSFORM ----------

def hash_key(*values):
    text = "|".join(str(v).strip().upper() for v in values)
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def convert_to_eur(payments, rates):
    payments = payments.sort_values("payment_date")
    rates = rates.sort_values("rate_date")
    merged = pd.merge_asof(
        payments,
        rates,
        left_on="payment_date",
        right_on="rate_date",
        by="currency",
        direction="backward",
    )
    merged.loc[merged["currency"] == "EUR", "exchange_rate"] = 1.0
    merged["amount_eur"] = (merged["amount"] / merged["exchange_rate"]).round(2)
    return merged.drop(columns="rate_date")


def build_customer_tables(customers):
    df = customers.copy()
    df["hk_customer"] = df["customer_id"].apply(hash_key)
    df["load_date"] = LOAD_DATE
    df["record_source"] = "customers.csv"
    df["hashdiff"] = df.apply(
        lambda r: hash_key(r["first_name"], r["last_name"], r["country"], r["iban"]), axis=1
    )

    hub = df[["hk_customer", "customer_id", "load_date", "record_source"]]
    sat = df[["hk_customer", "load_date", "hashdiff", "first_name", "last_name",
              "country", "iban", "record_source"]]
    return hub, sat


def build_payment_tables(payments):
    df = payments.copy()
    df["hk_payment"] = df["payment_id"].apply(hash_key)
    df["hk_customer"] = df["customer_id"].apply(hash_key)
    df["hk_customer_payment"] = df.apply(
        lambda r: hash_key(r["customer_id"], r["payment_id"]), axis=1
    )
    df["load_date"] = LOAD_DATE
    df["record_source"] = "payments.csv"
    df["hashdiff"] = df.apply(
        lambda r: hash_key(r["amount"], r["currency"], r["payment_date"]), axis=1
    )

    hub = df[["hk_payment", "payment_id", "load_date", "record_source"]]
    link = df[["hk_customer_payment", "hk_customer", "hk_payment", "load_date", "record_source"]]
    sat = df[["hk_payment", "load_date", "hashdiff", "amount", "currency", "exchange_rate",
              "amount_eur", "payment_date", "record_source"]]
    return hub, link, sat


# ---------- 4. LOAD ----------

def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)


def load_new_rows(df, table, key_columns, engine):
    existing = pd.read_sql(f"SELECT {', '.join(key_columns)} FROM {table}", engine)
    merged = df.merge(existing, on=key_columns, how="left", indicator=True)
    new_rows = merged[merged["_merge"] == "left_only"].drop(columns="_merge")
    new_rows.to_sql(table, engine, if_exists="append", index=False)
    print(f"{table}: {len(new_rows)} new rows")


def run():
    customers, payments = extract_csv()
    rates = extract_ecb_rates()

    good, bad = validate(payments, customers)
    good = convert_to_eur(good, rates)

    hub_customer, sat_customer = build_customer_tables(customers)
    hub_payment, link_customer_payment, sat_payment = build_payment_tables(good)

    errors = bad[["payment_id", "customer_id", "amount", "currency",
                  "payment_date", "error_reason"]].copy()
    errors["load_date"] = LOAD_DATE

    engine = get_engine()
    load_new_rows(hub_customer, "hub_customer", ["hk_customer"], engine)
    load_new_rows(hub_payment, "hub_payment", ["hk_payment"], engine)
    load_new_rows(link_customer_payment, "link_customer_payment", ["hk_customer_payment"], engine)
    load_new_rows(sat_customer, "sat_customer", ["hk_customer", "hashdiff"], engine)
    load_new_rows(sat_payment, "sat_payment", ["hk_payment", "hashdiff"], engine)
    load_new_rows(errors, "payment_errors", ["payment_id", "error_reason"], engine)


if __name__ == "__main__":
    run()