"""
JWT Authentication module
Simple user management + JWT tokens (file-based for now)
"""
import json
import os
import hashlib
import secrets
from datetime import timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, verify_jwt_in_request
)
from .config import Config

auth_bp = Blueprint('auth', __name__)

# User storage path
USERS_FILE = os.path.join(os.path.dirname(__file__), '../data/users.json')


def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def _save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def _hash_password(password):
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}:{hash_obj.hexdigest()}"


def _verify_password(password, stored):
    salt, hash_val = stored.split(':')
    hash_obj = hashlib.sha256((salt + password).encode())
    return hash_obj.hexdigest() == hash_val


def init_jwt(app):
    """Initialize JWT manager - call from create_app()"""
    jwt = JWTManager(app)

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({'error': 'Invalid token', 'reason': reason}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token expired'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({'error': 'Authorization required'}), 401

    return jwt


# Auth routes
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    username = data['username'].strip()
    password = data['password']
    if len(username) < 3 or len(password) < 6:
        return jsonify({'error': 'Username min 3 chars, password min 6 chars'}), 400
    users = _load_users()
    if username in users:
        return jsonify({'error': 'Username already exists'}), 409
    users[username] = {
        'password': _hash_password(password),
        'created_at': __import__('datetime').datetime.now().isoformat()
    }
    _save_users(users)
    token = create_access_token(identity=username)
    return jsonify({'token': token, 'username': username}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    username = data['username'].strip()
    password = data['password']
    users = _load_users()
    user = users.get(username)
    if not user or not _verify_password(password, user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_access_token(identity=username)
    return jsonify({'token': token, 'username': username}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    username = get_jwt_identity()
    return jsonify({'username': username}), 200
