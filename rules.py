from datetime import datetime

HIGH_RISK_COUNTRIES     = ['Iran', 'North Korea', 'Myanmar', 'Syria', 'Cuba']
STRUCTURING_THRESHOLD   = 950000
LARGE_CASH_THRESHOLD    = 1000000

RULE_SCORES = {
    "HIGH_RISK_COUNTRY":      95,
    "LARGE_CASH_TRANSACTION": 88,
    "STRUCTURING":            90,
    "PEP_HIGH_VALUE_WIRE":    85,
    "HIGH_VELOCITY":          60,
    "ROUND_TRIPPING":         65,
    "PROFILE_MISMATCH":       55,
    "MULTIPLE_JURISDICTIONS": 58,
    "NEW_CUSTOMER_LARGE_TXN": 25,
    "UNUSUAL_HOURS":          20,
}


def rule_high_risk_country(customer, transactions):
    flagged = [t for t in transactions if t.country in HIGH_RISK_COUNTRIES]
    if flagged:
        return {
            'rule': 'HIGH_RISK_COUNTRY',
            'severity': 'HIGH',
            'amount': sum(t.amount for t in flagged),
            'description': f'Transaction involving high-risk country: {flagged[0].country}'
        }

def rule_large_cash_transaction(customer, transactions):
    flagged = [t for t in transactions if t.txn_type == 'CASH_DEPOSIT' and t.amount >= LARGE_CASH_THRESHOLD]
    if flagged:
        return {
            'rule': 'LARGE_CASH_TRANSACTION',
            'severity': 'HIGH',
            'amount': flagged[0].amount,
            'description': f'Cash deposit of {flagged[0].amount:,.0f} exceeds reporting threshold'
        }

def rule_structuring(customer, transactions):
    suspicious = [t for t in transactions if t.txn_type == 'CASH_DEPOSIT' and 800000 <= t.amount <= STRUCTURING_THRESHOLD]
    if len(suspicious) >= 2:
        return {
            'rule': 'STRUCTURING',
            'severity': 'HIGH',
            'amount': sum(t.amount for t in suspicious),
            'description': f'{len(suspicious)} deposits clustered just below reporting threshold — possible structuring'
        }

def rule_pep_high_value_wire(customer, transactions):
    if customer.is_pep:
        flagged = [t for t in transactions if t.txn_type in ('WIRE_OUT', 'WIRE_IN') and t.amount >= 500000]
        if flagged:
            return {
                'rule': 'PEP_HIGH_VALUE_WIRE',
                'severity': 'HIGH',
                'amount': flagged[0].amount,
                'description': 'Politically exposed person conducting high-value wire transfer'
            }

def rule_high_velocity(customer, transactions):
    from collections import Counter
    dates = [t.timestamp.date() for t in transactions]
    for date, count in Counter(dates).items():
        if count >= 5:
            return {
                'rule': 'HIGH_VELOCITY',
                'severity': 'MEDIUM',
                'amount': sum(t.amount for t in transactions if t.timestamp.date() == date),
                'description': f'{count} transactions on {date} — unusual velocity'
            }

def rule_round_tripping(customer, transactions):
    outs = [t for t in transactions if t.txn_type == 'WIRE_OUT']
    ins  = [t for t in transactions if t.txn_type == 'WIRE_IN']
    for out in outs:
        for inp in ins:
            if abs(out.amount - inp.amount) / max(out.amount, 1) < 0.05:
                return {
                    'rule': 'ROUND_TRIPPING',
                    'severity': 'MEDIUM',
                    'amount': out.amount,
                    'description': 'Funds sent and returned in near-identical amount — possible round-tripping'
                }

def rule_profile_mismatch(customer, transactions):
    if customer.risk_level == 'LOW':
        flagged = [t for t in transactions if t.amount >= 500000]
        if flagged:
            return {
                'rule': 'PROFILE_MISMATCH',
                'severity': 'MEDIUM',
                'amount': flagged[0].amount,
                'description': f'Low-risk customer profile inconsistent with large transaction'
            }

def rule_multiple_jurisdictions(customer, transactions):
    countries = set(t.country for t in transactions if t.country)
    if len(countries) >= 3:
        return {
            'rule': 'MULTIPLE_JURISDICTIONS',
            'severity': 'MEDIUM',
            'amount': sum(t.amount for t in transactions),
            'description': f'Transactions spanning {len(countries)} countries: {", ".join(list(countries)[:3])}'
        }

def rule_new_customer_large_txn(customer, transactions):
    from datetime import timedelta
    if customer.created_at >= datetime.utcnow() - timedelta(days=90):
        flagged = [t for t in transactions if t.amount >= 200000]
        if flagged:
            return {
                'rule': 'NEW_CUSTOMER_LARGE_TXN',
                'severity': 'LOW',
                'amount': flagged[0].amount,
                'description': 'New customer with large transaction — monitor'
            }

def rule_unusual_hours(customer, transactions):
    odd = [t for t in transactions if t.timestamp.hour < 7 or t.timestamp.hour >= 22]
    if len(odd) >= 2:
        return {
            'rule': 'UNUSUAL_HOURS',
            'severity': 'LOW',
            'amount': sum(t.amount for t in odd),
            'description': f'{len(odd)} transactions at unusual hours'
        }


ALL_RULES = [
    rule_high_risk_country,
    rule_large_cash_transaction,
    rule_structuring,
    rule_pep_high_value_wire,
    rule_high_velocity,
    rule_round_tripping,
    rule_profile_mismatch,
    rule_multiple_jurisdictions,
    rule_new_customer_large_txn,
    rule_unusual_hours,
]


def run_all_rules(customer, transactions):
    results = []
    for rule_fn in ALL_RULES:
        result = rule_fn(customer, transactions)
        if result:
            results.append(result)
    return results