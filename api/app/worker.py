from celery import Celery

celery_app = Celery(
    "schenker_composer",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)


@celery_app.task
def ping() -> str:
    return "pong"
