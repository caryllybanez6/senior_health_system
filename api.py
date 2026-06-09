from datetime import date, datetime, time, timedelta
from decimal import Decimal

from flask import Blueprint, request, jsonify, session

from ai_priority import AIPriorityScorer
from db import Database

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _require_senior_session():
    if session.get('user_type') != 'senior' or 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    return None


def _serialize_db_value(value):
    if isinstance(value, dict):
        return {k: _serialize_db_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_db_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime('%H:%M:%S')
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def _get_appointment_by_id(appointment_id):
    return Database.execute_query(
        "SELECT * FROM appointments WHERE id = %s AND senior_id = %s",
        (appointment_id, session['user_id']),
        fetch_one=True
    )


def _book_appointment(data):
    service_type = data.get('service_type')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')
    symptoms = data.get('symptoms', '')
    is_emergency = bool(data.get('is_emergency'))

    if not service_type or not appointment_date or not appointment_time:
        return None, None, jsonify({
            'success': False,
            'error': 'Required fields: service_type, appointment_date, appointment_time'
        }), 400

    senior = Database.execute_query(
        'SELECT * FROM seniors WHERE id = %s',
        (session['user_id'],),
        fetch_one=True
    )
    if not senior:
        return None, None, jsonify({'success': False, 'error': 'Senior record not found'}), 404

    priority_score = AIPriorityScorer.calculate_total_priority(
        senior_age=senior.get('age', 0),
        symptoms=symptoms,
        is_emergency=is_emergency,
        waiting_minutes=0,
        medical_conditions=senior.get('medical_conditions', '')
    )

    appointment_id = Database.execute_query(
        """INSERT INTO appointments (senior_id, service_type, appointment_date, 
                                     appointment_time, priority_score, symptoms, is_emergency)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (session['user_id'], service_type, appointment_date,
         appointment_time, priority_score, symptoms, is_emergency)
    )
    if not appointment_id:
        return None, None, jsonify({'success': False, 'error': 'Failed to create appointment'}), 500

    return appointment_id, priority_score, None, None


@api_bp.route('/appointments', methods=['GET'])
def list_appointments():
    auth_error = _require_senior_session()
    if auth_error:
        return auth_error

    appointments = Database.execute_query(
        """SELECT a.*, q.queue_number, q.priority_score, q.estimated_wait_time
           FROM appointments a
           LEFT JOIN queue q ON a.id = q.appointment_id
           WHERE a.senior_id = %s
           ORDER BY a.appointment_date DESC""",
        (session['user_id'],),
        fetch_all=True
    ) or []

    serialized = [_serialize_db_value(item) for item in appointments]
    return jsonify(success=True, appointments=serialized)


@api_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    auth_error = _require_senior_session()
    if auth_error:
        return auth_error

    appointment = _get_appointment_by_id(appointment_id)
    if not appointment:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404

    return jsonify(success=True, appointment=_serialize_db_value(appointment))


@api_bp.route('/appointments', methods=['POST'])
def create_appointment():
    auth_error = _require_senior_session()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    appointment_id, priority_score, error_response, status_code = _book_appointment(data)
    if error_response is not None:
        return error_response, status_code

    return jsonify({
        'success': True,
        'appointment_id': appointment_id,
        'priority_score': priority_score,
        'message': 'Appointment created successfully.'
    }), 201


@api_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    auth_error = _require_senior_session()
    if auth_error:
        return auth_error

    appointment = _get_appointment_by_id(appointment_id)
    if not appointment:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404

    if appointment.get('status') not in ('pending', 'approved'):
        return jsonify({'success': False, 'error': 'Only pending or approved appointments can be updated.'}), 400

    data = request.get_json(silent=True) or {}
    updates = {}
    params = []

    for field in ('service_type', 'appointment_date', 'appointment_time', 'symptoms', 'is_emergency'):
        if field in data:
            updates[field] = data[field]

    if not updates:
        return jsonify({'success': False, 'error': 'No updatable fields provided.'}), 400

    if 'is_emergency' in updates:
        updates['is_emergency'] = bool(updates['is_emergency'])

    set_clause = ', '.join([f"{field} = %s" for field in updates])
    params = list(updates.values()) + [appointment_id]

    Database.execute_query(
        f"UPDATE appointments SET {set_clause} WHERE id = %s",
        tuple(params)
    )

    return jsonify({'success': True, 'appointment_id': appointment_id, 'message': 'Appointment updated successfully.'})


@api_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    auth_error = _require_senior_session()
    if auth_error:
        return auth_error

    appointment = _get_appointment_by_id(appointment_id)
    if not appointment:
        return jsonify({'success': False, 'error': 'Appointment not found'}), 404

    if appointment.get('status') in ('cancelled', 'completed', 'rejected'):
        return jsonify({'success': False, 'error': 'Appointment cannot be cancelled.'}), 400

    Database.execute_query(
        "UPDATE appointments SET status = 'cancelled' WHERE id = %s",
        (appointment_id,)
    )

    return jsonify({'success': True, 'appointment_id': appointment_id, 'message': 'Appointment cancelled successfully.'})


@api_bp.route('/senior/book', methods=['POST'])
def senior_book_api():
    return create_appointment()
