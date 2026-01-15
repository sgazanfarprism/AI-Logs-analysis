import json
from datetime import datetime, timedelta
import requests
import random

def seed_many_logs(count=100):
    es_url = "http://localhost:9200/filebeat-test/_doc"
    headers = {"Content-Type": "application/json"}
    
    now = datetime.utcnow()
    
    services = ["api-gateway", "user-service", "payment-service", "auth-service", "inventory-service"]
    error_types = ["ConnectionTimeout", "NullPointerException", "OutOfMemoryError", "ValidationError", "AccessDenied"]
    messages = [
        "Failed to connect to database",
        "Unexpected null value found",
        "System resources exhausted",
        "Invalid input parameters provided",
        "Insufficient permissions for operation"
    ]
    
    for i in range(count):
        service = random.choice(services)
        error_type = random.choice(error_types)
        message = random.choice(messages)
        
        log = {
            "@timestamp": (now - timedelta(minutes=random.randint(1, 60))).isoformat() + "Z",
            "message": message,
            "log": {"level": random.choice(["error", "critical", "warning"])},
            "service": {"name": service},
            "error": {"type": error_type, "message": f"{message} at step {i}"}
        }
        
        requests.post(es_url, headers=headers, data=json.dumps(log))
    
    print(f"Ingested {count} logs")

if __name__ == "__main__":
    seed_many_logs(100)
