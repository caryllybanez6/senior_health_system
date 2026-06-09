from app import app

app.testing = True
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['user_type'] = 'senior'
    sess['user_name'] = 'Juan Dela Cruz'

resp = client.post(
    '/api/appointments',
    json={
        'service_type': 'Medical Consult',
        'appointment_date': '2099-01-01',
        'appointment_time': '09:00',
        'symptoms': 'mild headache',
        'is_emergency': False,
    }
)
print('status', resp.status_code)
print('json', resp.get_json())
