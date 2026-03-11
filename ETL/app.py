from contextlib import asynccontextmanager

from fastapi import FastAPI

from Src.Components import execute_task, execute_util
from Src.Constants import APIStatus, TaskType
from Src.Utils import log_etl


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_etl.info("ETL service started")
    yield
    log_etl.info("ETL service shutting down")


app = FastAPI(title="ETL", lifespan=lifespan)

tasks: dict[TaskType, APIStatus] = {
    TaskType.SEED: APIStatus(task=TaskType.SEED),
    TaskType.SCRP: APIStatus(task=TaskType.SCRP),
    TaskType.LOAD: APIStatus(task=TaskType.LOAD),
}


@app.post("/seed")
def seeder():  # theres a bug where it loads 700 failed urls into redis
    return execute_task(TaskType.SEED, tasks)


@app.post("/scrape")
def scraper():
    return execute_task(TaskType.SCRP, tasks)


# i noticed some weird bug where it was failing after
# trying to get batch data from mongo when connecting to
# prod falkor. check once
@app.post("/load")
def loader():  # loads full dataset. fix it
    return execute_task(TaskType.LOAD, tasks)


@app.get("/health")
def health():
    return execute_util("health", tasks)


@app.get("/status")
def status(task: TaskType, task_id: str):
    return execute_util("status", tasks, task=task, task_id=task_id)


@app.get("/kill")
def kill(task: TaskType, task_id: str):
    return execute_util("kill", tasks, task=task, task_id=task_id)
