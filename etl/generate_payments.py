import random
from faker import Faker
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

fake= Faker("de_DE")
random.seed(42)
Faker.seed(42)
N_PAYMENTS= 500
N_USERS= 50
CURRENCIES= ["EUR", "USD", "GBP", "JPY", "CHF"]
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def make_customers():
    customers= []
    for i in range(N_USERS):
        customer= {
            "customer_id": i + 1,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "country": fake.country_code(),
            "iban": fake.iban(),
        }
        customers.append(customer)
    return customers

def make_payments(customers):
    payments= []
    for  i in range(N_PAYMENTS):
        customer= random.choice(customers)
        payment= {
            "payment_id": i + 1,
            "customer_id": customer["customer_id"],
            "amount": round(random.uniform(10, 1000), 2),
            "currency": random.choice(CURRENCIES),
            "payment_date": fake.date_time_between(start_date="-1y", end_date="now"),
        }
        payments.append(payment)
    return payments

def add_bad_rows(payments):
    payments[0]["amount"] = -50.00
    payments[10]["currency"] = None
    payments[20]["customer_id"] = 999
    payments.append(payments[30].copy())
    return payments

def main():
    DATA_DIR.mkdir(exist_ok=True)
    customers= make_customers()
    payments= make_payments(customers)
    payments= add_bad_rows(payments)
    df= pd.DataFrame(payments)
    df.to_csv(DATA_DIR / "payments.csv", index=False)
    df_customers= pd.DataFrame(customers)
    df_customers.to_csv(DATA_DIR / "customers.csv", index=False)

if __name__ == "__main__":
    main()