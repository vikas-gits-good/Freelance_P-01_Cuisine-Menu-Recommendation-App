import asyncio
import os
from multiprocessing import Process
from signal import SIGKILL
from threading import Thread
from typing import Literal, Optional
from uuid import uuid4

from falkordb.asyncio import FalkorDB as AsyncFalkorDB
from fastapi import HTTPException
from pymongo import AsyncMongoClient
from redis.asyncio import Redis as AsyncRedis

from Src.Config import FalkorDBConfig, MongoDBConfig, RedisDBConfig
from Src.Constants import APIStatus, TaskStatus, TaskType
from Src.Utils import LogException, log_etl

from .extractor import ETL_Scraper
from .loader import ETL_Loader
from .seeder import ETL_Seeder


class AplcOps:
    def __init__(self, task: APIStatus, purpose: TaskType = TaskType.SEED):
        try:
            log_etl.info(f"ETL_API: Received api call for '{purpose.value}'")
            self.task = task
            self.purpose = purpose

            # prevent concurrent runs on same api endpoint
            if self.task.status == TaskStatus.ONGOING:
                log_etl.info(
                    f"ETL_API: Concurrent call was made on endpoint '{purpose.value}' with task id: '{self.task.task_id}'"
                )

            # create new task with task_id
            else:
                log_etl.info(
                    f"ETL_API: New API call was made on endpoint '{purpose.value}'. Creating new task id"
                )
                self.task.task_id = uuid4().hex[:12]
                self.task.status = TaskStatus.ONGOING
                self.task.message = "all ok"

        except Exception as e:
            LogException(e, logger=log_etl)
            self.task.status = TaskStatus.ERROR

    def run(self):  # for getting status updates
        try:
            thread = Thread(
                target=self._run,
                args=(self.task.task_id,),
                daemon=True,
            )
            thread.start()
            _status = self.task.model_dump()

        except Exception as e:
            LogException(e, logger=log_etl)
            self.task.status = TaskStatus.ERROR
            _status = self.task.model_dump()

        return _status

    def _run(self, task_id: str):  # actual place where process is run
        try:
            callable = {
                TaskType.SEED: AplcOps._seeder,
                TaskType.SCRP: AplcOps._scrapr,
                TaskType.LOAD: AplcOps._loader,
            }.get(self.purpose, AplcOps._seeder)

            # create a multithread Process
            process = Process(
                target=callable,
                args=(task_id,),
                daemon=True,
            )
            process.start()

            # Set process group AFTER start, from parent
            try:
                os.setpgid(process.pid, process.pid)  # type: ignore[misc]

            except (ProcessLookupError, PermissionError):
                pass  # Process may have already exited

            # Store process reference for killing later
            self.task.process = process
            process.join()

            if process.exitcode == 0:
                self.task.status = TaskStatus.FINISHED

            elif process.exitcode in (-15, -9):
                self.task.status = TaskStatus.KILLED

            else:
                self.task.status = TaskStatus.FAILED

            self.task.process = None

        except Exception as e:
            LogException(e, logger=log_etl)
            self.task.status = TaskStatus.ERROR

    @staticmethod
    def _seeder(task_id: str):
        """Run seeder + upsert in a background thread and update task status."""
        try:
            # os.setpgrp()  # Setting a group so you can kill later by PID
            log_etl.info(f"ETL_API: Preparing ETL seeder for task '{task_id}'")
            sedr = ETL_Seeder()

            log_etl.info("ETL_API: Running ETL seeder")
            sedr.run_seeder()

            log_etl.info("ETL_API: Running ETL upsert")
            sedr.run_upsert()

            log_etl.info(f"ETL_API: Finished ETL seeder for task '{task_id}'")

        except Exception as e:
            LogException(e, logger=log_etl)
            # staticmethods return exit code 0 on error which will
            # make the system think it worked successfuly
            # that's why need to raise the error
            raise

    @staticmethod
    def _scrapr(task_id: str):
        """Run scraper + upsert in a background thread and update task status."""
        try:
            # os.setpgrp()  # Setting a group so you can kill later by PID
            log_etl.info(f"ETL_API: Preparing ETL scraper for task '{task_id}'")
            scrp = ETL_Scraper()

            log_etl.info("ETL_API: Running ETL scraper")
            scrp.run()

            log_etl.info(f"ETL_API: Finished ETL scraper for task '{task_id}'")

        except Exception as e:
            LogException(e, logger=log_etl)
            raise

    @staticmethod
    def _loader(task_id: str):
        try:
            # os.setpgrp()  # Setting a group so you can kill later by PID
            log_etl.info(f"ETL_API: Preparing ETL loader for task '{task_id}'")
            purpose = os.getenv("LOADER_PURPOSE", "prod")
            lodr = ETL_Loader(purpose)  # type:ignore

            log_etl.info("ETL_API: Running ETL loader")
            lodr.run()

            log_etl.info(f"ETL_API: Finished ETL loader for task '{task_id}'")

        except Exception as e:
            LogException(e, logger=log_etl)
            raise


class UtilOps:
    def __init__(
        self,
        tool: Literal["health", "status", "kill"] = "health",
        tasks: Optional[dict[TaskType, APIStatus]] = None,
    ):
        try:
            self.tool = tool
            self.tasks = tasks or {}

        except Exception as e:
            LogException(e, logger=log_etl)

    def run(self, **kwargs):
        try:
            func = {
                "health": self._health_check,  # async tool
                "status": self._status_check,
                "kill": self._kill_switch,
            }.get(self.tool, self._health_check)

            # Handle async tools
            if asyncio.iscoroutinefunction(func):
                status = asyncio.run(func(**kwargs))
            else:
                status = func(**kwargs)

        except Exception as e:
            LogException(e, logger=log_etl)
            status = {"status": "error"}

        return status

    async def _health_check(self):
        """Async health check - pings all databases in parallel for faster response."""
        status = {"status": "ok", "mongo": "ok", "redis": "ok", "falkor": "ok"}

        async def check_mongo():
            try:
                mg_cnf = MongoDBConfig()
                client = AsyncMongoClient(
                    mg_cnf.conn_uri,
                    serverSelectionTimeoutMS=5000,
                )
                await client.admin.command("ping")
                await client.close()

            except Exception as e:
                log_etl.info("ETL_API: Health check FAIL (MongoDB)")
                LogException(e, logger=log_etl)
                status["mongo"] = "unreachable"
                status["status"] = "degraded"

        async def check_redis():
            try:
                rd_cnf = RedisDBConfig()
                client = AsyncRedis(
                    **rd_cnf.redis_dict_main,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                await client.ping()  # type: ignore[misc]
                await client.aclose()

            except Exception as e:
                log_etl.info("ETL_API: Health check FAIL (RedisDB)")
                LogException(e, logger=log_etl)
                status["redis"] = "unreachable"
                status["status"] = "degraded"

        async def check_falkor():
            try:
                fd_cnf = FalkorDBConfig()
                fdb = AsyncFalkorDB(**fd_cnf.conn_dict, socket_timeout=5)
                graph = fdb.select_graph(fd_cnf.fdb_kg)
                await graph.query("RETURN 1")

            except Exception as e:
                log_etl.info("ETL_API: Health check FAIL (FalkorDB)")
                LogException(e, logger=log_etl)
                status["falkor"] = "unreachable"
                status["status"] = "degraded"

        # Run all health checks in parallel
        await asyncio.gather(
            check_mongo(),
            check_redis(),
            check_falkor(),
            return_exceptions=True,  # Continue even if one fails
        )

        return status

    def _status_check(self, task: TaskType, task_id: str):
        try:
            entry = self.tasks[task]

            if entry.task_id != task_id:
                entry.status = TaskStatus.ERROR
                entry.message = "Wrong task_id"

        except Exception as e:
            LogException(e, logger=log_etl)
            entry.status = TaskStatus.ERROR
            entry.message = f"Unknown error: {str(e)}"

        return entry.model_dump()

    def _kill_switch(self, task: TaskType, task_id: str):
        try:
            entry = self.tasks[task]

            # Check for wrong task_id
            if entry.task_id != task_id:
                log_etl.info(
                    f"ETL_API: Failed to kill '{task}: {task_id}' as it is wrong task_id (status: {entry.status.value})"
                )
                entry.status = TaskStatus.ERROR
                entry.message = "Wrong task_id"

            # check for task status
            elif entry.status != TaskStatus.ONGOING:
                log_etl.info(
                    f"ETL_API: Failed to kill '{task}: {task_id}' as it is not running (status: {entry.status.value})"
                )
                entry.status = TaskStatus.ERROR
                entry.message = "Task isn't running"

            # check for process
            elif not entry.process or not entry.process.is_alive():
                log_etl.info(
                    f"ETL_API: Failed to kill '{task}: {task_id}' as process is not present (status: {entry.status.value})"
                )
                entry.status = TaskStatus.ERROR
                entry.message = "Program is missing"

            else:
                # Force kill
                if entry.process.is_alive():
                    log_etl.info(f"ETL_API: Sending SIGKILL to kill task '{task_id}'")
                    os.killpg(os.getpgid(entry.process.pid), SIGKILL)  # type: ignore[misc]

                entry.status = TaskStatus.KILLED
                entry.message = "Successfully killed task"
                entry.process = None
                log_etl.info(f"ETL_API: Successfully killed task '{task_id}'")

        except Exception as e:
            LogException(e, logger=log_etl)
            entry.status = TaskStatus.ERROR
            entry.message = f"Unknown error: {str(e)}"

        return entry.model_dump()


# ============================================================================
# FastAPI Endpoint Helpers
# ============================================================================


def execute_task(task_type: TaskType, tasks: dict[TaskType, APIStatus]):
    """Helper function to execute ETL tasks with FastAPI error handling.

    Args:
        task_type: The type of task to execute (SEED, SCRP, LOAD)
        tasks: Dictionary mapping task types to their status

    Returns:
        Task execution status

    Raises:
        HTTPException: If task execution fails
    """
    try:
        log_etl.info(f"ETL_API: Starting task: {task_type.value}")
        aplc = AplcOps(tasks[task_type], task_type)
        result = aplc.run()
        log_etl.info(f"ETL_API: Task {task_type.value} executed successfully")

    except Exception as e:
        log_etl.error(f"Task {task_type.value} failed: {str(e)}", exc_info=True)
        LogException(e, logger=log_etl)

        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")

    return result


def execute_util(
    tool: Literal["health", "status", "kill"],
    tasks: dict[TaskType, APIStatus],
    **kwargs,
):
    """Helper function to execute utility operations with FastAPI error handling.

    Args:
        tool: The utility tool to execute (health, status, kill)
        tasks: Dictionary mapping task types to their status
        **kwargs: Additional arguments to pass to the utility operation

    Returns:
        Utility operation result

    Raises:
        HTTPException: If utility operation fails
    """
    try:
        log_etl.info(f"ETL_API: Executing utility: {tool}")
        util = UtilOps(tool=tool, tasks=tasks if tool in ["status", "kill"] else None)
        result = util.run(**kwargs)
        log_etl.info(f"ETL_API: Utility {tool} executed successfully")

    except Exception as e:
        log_etl.error(f"ETL_API: Utility {tool} failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"{tool.capitalize()} operation failed: {str(e)}"
        )

    return result
