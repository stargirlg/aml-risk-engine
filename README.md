# AML Risk Engine API

A production-grade Anti-Money Laundering (AML) transaction monitoring API built with Python and Flask.

## What it does
Detects suspicious financial transactions using 10 rule-based detection algorithms based on real FATF AML guidelines.

## Tech Stack
- Python 3
- Flask
- SQLAlchemy
- SQLite
- Gunicorn
- Render (deployment)

## 10 Detection Rules

| Rule | Severity | Score |
|------|----------|-------|
| High-risk country | HIGH | 95 |
| Structuring | HIGH | 90 |
| Large cash transaction | HIGH | 88 |
| PEP high-value wire | HIGH | 85 |
| Round-tripping | MEDIUM | 65 |
| High velocity | MEDIUM | 60 |
| Multiple jurisdictions | MEDIUM | 58 |
| Profile mismatch | MEDIUM | 55 |
| New customer large transaction | LOW | 25 |
| Unusual hours | LOW | 20 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /customers | List all customers |
| GET | /customers?name=Ravi | Search by name |
| GET | /alerts | All alerts sorted by risk score |
| GET | /alerts?severity=HIGH | Filter by severity |
| GET | /rules | All 10 rules with scores |
| POST | /screen | Run rules against customer |
| PATCH | /alerts/<id>/status | Update alert status |

## Features
- ✅ Risk scoring 0-100 for alert prioritization
- ✅ Duplicate alert prevention
- ✅ Alert suppression for reviewed cases
- ✅ 5 alert statuses (OPEN, UNDER_REVIEW, ESCALATED, FALSE_POSITIVE, CLOSED)
- ✅ Full audit log for every status change
- ✅ Auto-seeds 10 fake customers on startup

## Setup locally

```bash
git clone https://github.com/stargirlg/aml-risk-engine
cd aml-risk-engine
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```

## Author
Gayatri Gohate — AML Analyst turned Backend Developer
