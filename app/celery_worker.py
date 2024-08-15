from celery import Celery


celery = Celery(
    'tasks',
    broker='amqp://guest:guest@rabbitmq',
    backend='db+postgresql://myuser:mypassword@db/mydatabase'
)
@celery.task
def example_task():
    # Simulate a long-running task
    import time
    time.sleep(10)
    return "Task completed"