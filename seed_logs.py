import json
from datetime import datetime, timedelta
import requests

def seed_logs():
    es_url = "http://localhost:9200/filebeat-test/_doc"
    headers = {"Content-Type": "application/json"}
    
    now = datetime.utcnow()
    
    logs = [
        {
            "@timestamp": (now - timedelta(minutes=5)).isoformat() + "Z",
            "message": "Connection timeout to database",
            "log": {"level": "error"},
            "service": {"name": "api-gateway"},
            "error": {"type": "ConnectionTimeout", "message": "Failed to connect to db:5432"}
        },
        {
            "@timestamp": (now - timedelta(minutes=4)).isoformat() + "Z",
            "message": "NullPointerException in UserService",
            "log": {"level": "error"},
            "service": {"name": "user-service"},
            "error": {"type": "NullPointerException", "message": "object is null"}
        },
        {
            "@timestamp": (now - timedelta(minutes=3)).isoformat() + "Z",
            "message": "Out of memory",
            "log": {"level": "critical"},
            "service": {"name": "payment-service"},
            "error": {"type": "OutOfMemoryError"}
        }
    ]
    
    for log in logs:
        resp = requests.post(es_url, headers=headers, data=json.dumps(log))
        print(f"Ingested log: {resp.status_code}")

if __name__ == "__main__":
    seed_logs()
