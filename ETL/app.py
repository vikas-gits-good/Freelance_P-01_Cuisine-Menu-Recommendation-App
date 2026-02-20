from contextlib import asynccontextmanager

from fastapi import FastAPI

from Src.Components import AplcOps, UtilOps
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
def seeder():
    purpose = TaskType.SEED
    aplc = AplcOps(tasks[purpose], purpose)
    return aplc.run()


@app.post("/scrape")
def scraper():
    purpose = TaskType.SCRP
    aplc = AplcOps(tasks[purpose], purpose)
    return aplc.run()


@app.post("/load")
def loader():
    purpose = TaskType.LOAD
    aplc = AplcOps(tasks[purpose], purpose)
    return aplc.run()


@app.get("/health")
def health():
    util = UtilOps(tool="health")
    return util.run()  # No kwargs here


@app.get("/status")
def status(task: TaskType, task_id: str):
    util = UtilOps(tool="status", tasks=tasks)
    return util.run(task=task, task_id=task_id)


@app.get("/kill")
def kill(task: TaskType, task_id: str):
    util = UtilOps(tool="kill", tasks=tasks)
    return util.run(task=task, task_id=task_id)
