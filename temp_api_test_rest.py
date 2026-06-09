from app import app

app.testing = True
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['user_type'] = 'senior'
    sess['user_name'] = 'Juan Dela Cruz'

# 1) Create a new appointment
create_resp = client.post(
    '/api/appointments',
    json={
        'service_type': 'Medical Consult',
        'appointment_date': '2099-01-01',
        'appointment_time': '09:00',
        'symptoms': 'mild headache',
        'is_emergency': False,
    }
)
print('CREATE status', create_resp.status_code)
print('CREATE json', create_resp.get_json())

create_data = create_resp.get_json() or {}
appointment_id = create_data.get('appointment_id')

if appointment_id:
    # 2) Get the created appointment
    get_resp = client.get(f'/api/appointments/{appointment_id}')
    print('GET status', get_resp.status_code)
    print('GET json', get_resp.get_json())

    # 3) List all appointments for the senior
    list_resp = client.get('/api/appointments')
    print('LIST status', list_resp.status_code)
    print('LIST json', list_resp.get_json())

    # 4) Update the appointment
    update_resp = client.put(
        f'/api/appointments/{appointment_id}',
        json={
            'symptoms': 'mild headache and dizziness',
            'is_emergency': True,
        }
    )
    print('UPDATE status', update_resp.status_code)
    print('UPDATE json', update_resp.get_json())

    # 5) Cancel the appointment
    delete_resp = client.delete(f'/api/appointments/{appointment_id}')
    print('DELETE status', delete_resp.status_code)
    print('DELETE json', delete_resp.get_json())
else:
    print('Could not create appointment; skipping GET/PUT/DELETE tests.')
