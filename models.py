from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Customer(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    country    = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    risk_level = db.Column(db.String(20))   # HIGH / MEDIUM / LOW
    is_pep     = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='customer', lazy=True)
    alerts       = db.relationship('Alert', backref='customer', lazy=True)


class Transaction(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    amount      = db.Column(db.Float)
    currency    = db.Column(db.String(10), default='INR')
    txn_type    = db.Column(db.String(50))   # CASH_DEPOSIT / WIRE_IN / WIRE_OUT
    country     = db.Column(db.String(100))  # counterparty country
    description = db.Column(db.String(200))
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)


class Alert(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    customer_id    = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    rule_triggered = db.Column(db.String(100))
    severity       = db.Column(db.String(20))
    risk_score     = db.Column(db.Integer, default=0)
    amount         = db.Column(db.Float)
    description    = db.Column(db.String(300))
    status         = db.Column(db.String(30), default='OPEN')
    suppressed     = db.Column(db.Boolean, default=False)
    analyst_notes  = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    alert_id   = db.Column(db.Integer, db.ForeignKey('alert.id'), nullable=False)
    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30))
    changed_by = db.Column(db.String(100))
    notes      = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)