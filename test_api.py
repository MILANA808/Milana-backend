#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новых эндпоинтов API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_root():
    """Тест корневого эндпоинта"""
    print("Testing GET /")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_health():
    """Тест health эндпоинта"""
    print("Testing GET /health")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_metrics():
    """Тест метрик"""
    print("Testing GET /aksi/metrics")
    response = requests.get(f"{BASE_URL}/aksi/metrics")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_ai_work_session():
    """Тест AI work session tracking"""
    print("Testing AI Work Session Tracking")

    # Start session
    print("1. Starting session...")
    response = requests.post(f"{BASE_URL}/aksi/ai-work/session", json={
        "action": "start",
        "metadata": {"task": "test implementation"}
    })
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    session_id = data["session_id"]
    print()

    time.sleep(1)

    # Update session
    print("2. Updating session...")
    response = requests.post(f"{BASE_URL}/aksi/ai-work/session", json={
        "action": "update",
        "session_id": session_id,
        "files_modified": ["main.py", "test_api.py"],
        "lines_changed": 150,
        "language": "python",
        "operation": "create",
        "commit_hash": "abc123def456"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

    time.sleep(1)

    # End session
    print("3. Ending session...")
    response = requests.post(f"{BASE_URL}/aksi/ai-work/session", json={
        "action": "end",
        "session_id": session_id
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

    # Get sessions
    print("4. Getting all sessions...")
    response = requests.get(f"{BASE_URL}/aksi/ai-work/sessions")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_crypto_keys():
    """Тест записи криптографических ключей"""
    print("Testing Crypto Key Recording")

    # Record key
    print("1. Recording crypto key...")
    response = requests.post(f"{BASE_URL}/aksi/crypto/record-key", json={
        "key_type": "ed25519",
        "public_key": "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEATestKeyDataHere123456789==\n-----END PUBLIC KEY-----",
        "purpose": "signing",
        "algorithm": "Ed25519",
        "created_by": "AI-Test-Agent",
        "metadata": {"test": True, "environment": "development"}
    })
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    key_id = data["key_id"]
    print()

    # Get all keys
    print("2. Getting all crypto keys...")
    response = requests.get(f"{BASE_URL}/aksi/crypto/keys")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

    # Get specific key
    print(f"3. Getting specific key {key_id}...")
    response = requests.get(f"{BASE_URL}/aksi/crypto/keys/{key_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_updated_metrics():
    """Тест обновлённых метрик после операций"""
    print("Testing Updated Metrics")
    response = requests.get(f"{BASE_URL}/aksi/metrics")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("=" * 80)
    print("AKSI Backend API Tests")
    print("=" * 80)
    print()

    try:
        test_root()
        test_health()
        test_metrics()
        test_ai_work_session()
        test_crypto_keys()
        test_updated_metrics()

        print("=" * 80)
        print("All tests completed!")
        print("=" * 80)
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Make sure it's running:")
        print("  python main.py")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
