from flask import Flask, request, jsonify
from models import db, Customer, Transaction, Alert, AuditLog
from rules import RULE_SCORES, run_all_rules, ALL_RULES
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def home():
    return jsonify({'message': 'AML Risk Engine Running'})

@app.route('/customers', methods=['GET'])
def get_customers():
    name = request.args.get('name', '')
    q = Customer.query
    if name:
        q = q.filter(Customer.name.ilike(f'%{name}%'))
    return jsonify([{'id': c.id, 'name': c.name, 'country': c.country,
                     'risk_level': c.risk_level, 'is_pep': c.is_pep} for c in q.all()])

@app.route('/alerts', methods=['GET'])
def get_alerts():
    severity = request.args.get('severity')
    status   = request.args.get('status')
    q = Alert.query.filter_by(suppressed=False)
    if severity:
        q = q.filter_by(severity=severity.upper())
    if status:
        q = q.filter_by(status=status.upper())
    alerts = q.order_by(Alert.risk_score.desc(), Alert.created_at.desc()).all()
    return jsonify([{'id': a.id, 'customer_id': a.customer_id, 'rule': a.rule_triggered,
                     'severity': a.severity, 'risk_score': a.risk_score, 'amount': a.amount,
                     'description': a.description, 'status': a.status,
                     'created_at': str(a.created_at)} for a in alerts])

@app.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    a = Alert.query.get_or_404(alert_id)
    c = Customer.query.get(a.customer_id)
    return jsonify({'alert': {'id': a.id, 'rule': a.rule_triggered, 'severity': a.severity,
                              'risk_score': a.risk_score, 'amount': a.amount,
                              'status': a.status, 'analyst_notes': a.analyst_notes},
                    'customer': {'name': c.name, 'country': c.country,
                                 'risk_level': c.risk_level, 'is_pep': c.is_pep}})

@app.route('/alerts/<int:alert_id>/status', methods=['PATCH'])
def update_alert_status(alert_id):
    VALID = ['OPEN', 'UNDER_REVIEW', 'ESCALATED', 'FALSE_POSITIVE', 'CLOSED']
    data = request.get_json()
    alert = Alert.query.get_or_404(alert_id)
    new_status = data.get('status', '').upper()
    if new_status not in VALID:
        return jsonify({'error': f'Use one of: {VALID}'}), 400
    old_status = alert.status
    alert.status = new_status
    if data.get('notes'):
        alert.analyst_notes = data['notes']
    db.session.add(AuditLog(alert_id=alert_id, old_status=old_status,
                            new_status=new_status, changed_by=data.get('analyst', 'unknown'),
                            notes=data.get('notes', '')))
    db.session.commit()
    return jsonify({'alert_id': alert_id, 'status': new_status,
                    'message': f'Updated: {old_status} → {new_status}'})

@app.route('/rules', methods=['GET'])
def list_rules():
    return jsonify([{'id': i+1, 'name': fn.__name__.replace('rule_','').upper(),
                     'score': RULE_SCORES.get(fn.__name__.replace('rule_','').upper(), 50)}
                    for i, fn in enumerate(ALL_RULES)])

@app.route('/customers/<int:customer_id>/alerts', methods=['GET'])
def customer_alerts(customer_id):
    Customer.query.get_or_404(customer_id)
    alerts = Alert.query.filter_by(customer_id=customer_id, suppressed=False)\
                        .order_by(Alert.risk_score.desc()).all()
    return jsonify([{'id': a.id, 'rule': a.rule_triggered, 'severity': a.severity,
                     'risk_score': a.risk_score, 'status': a.status,
                     'created_at': str(a.created_at)} for a in alerts])

@app.route('/screen', methods=['POST'])
def screen_customer():
    data = request.get_json()
    customer = Customer.query.get_or_404(data.get('customer_id'))
    transactions = Transaction.query.filter_by(customer_id=customer.id).all()
    triggered = run_all_rules(customer, transactions)
    results = []
    for result in triggered:
        rule  = result['rule']
        score = RULE_SCORES.get(rule, 50)
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if Alert.query.filter_by(customer_id=customer.id, rule_triggered=rule)\
                      .filter(Alert.created_at >= today).first():
            results.append({**result, 'risk_score': score, 'suppressed': True,
                            'reason': 'duplicate — already raised today'})
            continue
        recent = Alert.query.filter_by(customer_id=customer.id, rule_triggered=rule)\
                            .filter(Alert.status.in_(['CLOSED','FALSE_POSITIVE']),
                                    Alert.created_at >= datetime.utcnow() - timedelta(days=30)).first()
        if recent:
            results.append({**result, 'risk_score': score, 'suppressed': True,
                            'reason': f'suppressed — reviewed {recent.status} within 30 days'})
            continue
        db.session.add(Alert(customer_id=customer.id, rule_triggered=rule,
                             severity=result['severity'], risk_score=score,
                             amount=result['amount'], description=result['description']))
        results.append({**result, 'risk_score': score, 'suppressed': False})
    db.session.commit()
    raised = [r for r in results if not r['suppressed']]
    return jsonify({'customer': customer.name, 'alerts_raised': len(raised),
                    'alerts_suppressed': len(results) - len(raised),
                    'results': sorted(results, key=lambda x: x['risk_score'], reverse=True)})


# Auto seed on startup
with app.app_context():
    db.create_all()
    from models import Customer
    if Customer.query.count() == 0:
        from seed import seed_data
        seed_data()

if __name__ == '__main__':
    app.run(debug=True)