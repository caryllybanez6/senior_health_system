from app import app

app.testing = True
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['user_type'] = 'senior'
    sess['user_name'] = 'Juan Dela Cruz'

resp = client.get('/api/senior/appointments')
print('status', resp.status_code)
print('json', resp.get_json())
