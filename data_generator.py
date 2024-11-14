import os
import json
import random
import string
import time
from confluent_kafka import Producer
from datetime import datetime

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'test_topic')

# Initialize Kafka Producer
producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'linger.ms': 10,
    'batch.num.messages': 100
}

producer = Producer(**producer_conf)

def delivery_report(err, msg):
    """Callback for message delivery reports."""
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def generate_random_record():
    """
    Generates a random JSON record.
    """
    return {
        'record_key': ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
        'partition_path': 'partition_' + str(random.randint(1, 5)),
        'value': random.randint(1, 100),
        'timestamp': datetime.utcnow().isoformat()
    }

def send_records(num_records, interval):
    """
    Sends a specified number of records to Kafka at defined intervals.
    """
    for _ in range(num_records):
        record = generate_random_record()
        producer.produce(KAFKA_TOPIC, value=json.dumps(record), callback=delivery_report)
        producer.poll(0)  # Serve delivery reports (callbacks)
        print(f"Sent record: {record}")
        time.sleep(interval)
    producer.flush()

if __name__ == "__main__":
    NUM_RECORDS = 100  # Total number of records to send
    INTERVAL = 1       # Interval in seconds between records

    try:
        send_records(NUM_RECORDS, INTERVAL)
    except KeyboardInterrupt:
        print("Data generation interrupted.")
    finally:
        producer.flush()

