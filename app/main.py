from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from celery.result import AsyncResult
from celery_worker import example_task  # Import the Celery task
import pika
import psycopg2
import celery_worker
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def connect_to_rabbitmq(retries=5, delay=5):
    while retries > 0:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            return connection
        except pika.exceptions.AMQPConnectionError:
            retries -= 1
            print(f"RabbitMQ connection failed, retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Failed to connect to RabbitMQ after several retries")

connection = connect_to_rabbitmq()
channel = connection.channel()

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="mydatabase",
    user="myuser",
    password="mypassword",
    host="db",
    port="5432"
)
cur = conn.cursor()

@app.post("/run-task")
def run_task():
    task = example_task.delay()
    return {"task_id": task.id}

@app.get("/task-status/{task_id}")
def task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_worker.celery)
    if task_result.state == 'PENDING':
        response = {
            "state": task_result.state,
            "status": "Pending..."
        }
    elif task_result.state != 'FAILURE':
        response = {
            "state": task_result.state,
            "status": task_result.info
        }
    else:
        response = {
            "state": task_result.state,
            "status": str(task_result.info)
        }
    return response
