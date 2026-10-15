SCHEMA_DOCS = [
    {
        "table": "hub_customer",
        "description": (
            "hub_customer: one row per customer (Data Vault hub). "
            "Columns: hk_customer (hash key, CHAR(32)), customer_id (INTEGER business key), "
            "load_date, record_source. "
            "Use it to count customers or to join customers with payments."
        ),
    },
    {
        "table": "sat_customer",
        "description": (
            "sat_customer: customer details (Data Vault satellite). "
            "Columns: hk_customer (joins to hub_customer.hk_customer), load_date, hashdiff, "
            "first_name, last_name, country (2-letter ISO code like DE, FR), iban, record_source. "
            "Use it for customer names, countries and IBANs."
        ),
    },
    {
        "table": "hub_payment",
        "description": (
            "hub_payment: one row per payment (Data Vault hub). "
            "Columns: hk_payment (hash key), payment_id (INTEGER business key), "
            "load_date, record_source. "
            "Use it to count payments or to look up a payment by payment_id."
        ),
    },
    {
        "table": "sat_payment",
        "description": (
            "sat_payment: payment details (Data Vault satellite). "
            "Columns: hk_payment (joins to hub_payment.hk_payment), load_date, hashdiff, "
            "amount (original amount), currency (EUR, USD, GBP, JPY, CHF), "
            "exchange_rate (ECB rate, 1 EUR = x currency), amount_eur (amount converted to euro), "
            "payment_date (TIMESTAMP), record_source. "
            "Use amount_eur for totals, sums, averages and comparisons in euro."
        ),
    },
    {
        "table": "link_customer_payment",
        "description": (
            "link_customer_payment: connects customers and payments (Data Vault link). "
            "Columns: hk_customer_payment, hk_customer (joins to hub_customer and sat_customer), "
            "hk_payment (joins to hub_payment and sat_payment), load_date, record_source. "
            "Always use this table to find which customer made which payment. "
            "Join path: sat_customer.hk_customer = link_customer_payment.hk_customer "
            "and link_customer_payment.hk_payment = sat_payment.hk_payment."
        ),
    },
    {
        "table": "payment_errors",
        "description": (
            "payment_errors: payments rejected by data quality checks (quarantine table). "
            "Columns: payment_id, customer_id, amount, currency, payment_date, "
            "error_reason (e.g. 'amount not positive', 'missing currency', "
            "'unknown customer_id', 'duplicate payment_id'), load_date. "
            "Use it for questions about errors, rejected or invalid payments."
        ),
    },
]