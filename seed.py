from app import app
from models import db, Customer, Transaction, Alert
from datetime import datetime, timedelta

with app.app_context():
    db.drop_all()
    db.create_all()

    # ── Customers ────────────────────────────────────────────
    customers = [
        Customer(name="Ravi Mehta",    country="India",     occupation="Businessman",   risk_level="HIGH",   is_pep=False),
        Customer(name="Priya Sharma",  country="India",     occupation="PEP - MLA",     risk_level="HIGH",   is_pep=True),
        Customer(name="Ali Hassan",    country="Iran",      occupation="Trader",         risk_level="HIGH",   is_pep=False),
        Customer(name="Chen Wei",      country="China",     occupation="Importer",       risk_level="MEDIUM", is_pep=False),
        Customer(name="Sara Patel",    country="India",     occupation="Freelancer",     risk_level="LOW",    is_pep=False),
        Customer(name="James Okoro",   country="Nigeria",   occupation="Export Agent",   risk_level="MEDIUM", is_pep=False),
        Customer(name="Meena Nair",    country="India",     occupation="Housewife",      risk_level="LOW",    is_pep=False),
        Customer(name="Viktor Petrov", country="Russia",    occupation="Consultant",     risk_level="MEDIUM", is_pep=False),
        Customer(name="Anita Joseph",  country="India",     occupation="Student",        risk_level="LOW",    is_pep=False),
        Customer(name="David Lim",     country="Singapore", occupation="Retired Banker", risk_level="MEDIUM", is_pep=False),
    ]
    db.session.add_all(customers)
    db.session.commit()

    # ── Transactions (designed to trigger each rule) ──────────
    now = datetime.utcnow()
    transactions = [
        # Ravi — structuring (2 deposits just below 10L)
        Transaction(customer_id=1, amount=920000, txn_type='CASH_DEPOSIT', country='India', timestamp=now - timedelta(days=1)),
        Transaction(customer_id=1, amount=930000, txn_type='CASH_DEPOSIT', country='India', timestamp=now - timedelta(days=2)),

        # Priya — PEP wire
        Transaction(customer_id=2, amount=750000, txn_type='WIRE_OUT', country='UAE', timestamp=now - timedelta(days=1)),

        # Ali — high-risk country
        Transaction(customer_id=3, amount=500000, txn_type='WIRE_OUT', country='Iran', timestamp=now - timedelta(days=1)),

        # Chen — multiple jurisdictions
        Transaction(customer_id=4, amount=400000, txn_type='WIRE_OUT', country='China',     timestamp=now - timedelta(days=3)),
        Transaction(customer_id=4, amount=400000, txn_type='WIRE_OUT', country='Hong Kong', timestamp=now - timedelta(days=2)),
        Transaction(customer_id=4, amount=400000, txn_type='WIRE_OUT', country='UAE',       timestamp=now - timedelta(days=1)),

        # Sara — profile mismatch (low-risk, large txn)
        Transaction(customer_id=5, amount=600000, txn_type='WIRE_IN', country='India', timestamp=now - timedelta(days=1)),

        # James — round tripping
        Transaction(customer_id=6, amount=400000, txn_type='WIRE_OUT', country='Nigeria', timestamp=now - timedelta(days=2)),
        Transaction(customer_id=6, amount=398000, txn_type='WIRE_IN',  country='Nigeria', timestamp=now - timedelta(days=1)),

        # Meena — high velocity (5 txns same day)
        Transaction(customer_id=7, amount=50000, txn_type='CASH_DEPOSIT', country='India', timestamp=now.replace(hour=9)),
        Transaction(customer_id=7, amount=60000, txn_type='CASH_DEPOSIT', country='India', timestamp=now.replace(hour=10)),
        Transaction(customer_id=7, amount=55000, txn_type='CASH_DEPOSIT', country='India', timestamp=now.replace(hour=11)),
        Transaction(customer_id=7, amount=70000, txn_type='CASH_DEPOSIT', country='India', timestamp=now.replace(hour=12)),
        Transaction(customer_id=7, amount=65000, txn_type='CASH_DEPOSIT', country='India', timestamp=now.replace(hour=13)),

        # Viktor — large cash deposit
        Transaction(customer_id=8, amount=1500000, txn_type='CASH_DEPOSIT', country='Russia', timestamp=now - timedelta(days=1)),

        # Anita — unusual hours
        Transaction(customer_id=9, amount=40000, txn_type='WIRE_OUT', country='India', timestamp=now.replace(hour=23)),
        Transaction(customer_id=9, amount=40000, txn_type='WIRE_OUT', country='India', timestamp=now.replace(hour=1)),

        # David — new customer large txn (created_at will be recent by default)
        Transaction(customer_id=10, amount=250000, txn_type='WIRE_IN', country='Singapore', timestamp=now - timedelta(days=1)),
    ]
    db.session.add_all(transactions)
    db.session.commit()

    print("✅ Seeded 10 customers + transactions successfully")
    print("Run: flask run  OR  python app.py")