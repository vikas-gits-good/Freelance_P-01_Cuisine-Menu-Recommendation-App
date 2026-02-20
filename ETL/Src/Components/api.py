import os
from multiprocessing import Process
from signal import SIGKILL
from threading import Thread
from typing import Literal, Optional
from uuid import uuid4

from falkordb import FalkorDB
from pymongo import MongoClient
from redis import Redis

from Src.Config import FalkorDBConfig, MongoDBConfig, RedisDBConfig
from Src.Constants import APIStatus, StatusMessage, TaskStatus, TaskType
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
                os.setpgid(process.pid, process.pid)
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
            # make the system this it worked successfuly
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
            lodr = ETL_Loader()

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
                "health": self._health_check,
                "status": self._status_check,
                "kill": self._kill_switch,
            }.get(self.tool, self._health_check)

            status = func(**kwargs)

        except Exception as e:
            LogException(e, logger=log_etl)
            status = {"status": "error"}

        return status

    def _health_check(self):  # dont log here cuz it checks health frequently
        status = {"status": "ok", "mongo": "ok", "redis": "ok", "falkor": "ok"}
        try:
            mg_cnf = MongoDBConfig()
            with MongoClient(mg_cnf.conn_uri, serverSelectionTimeoutMS=5000) as client:
                client.admin.command("ping")

        except Exception as e:
            log_etl.info("ETL_API: Status: FAIL")
            LogException(e, logger=log_etl)
            status["mongo"] = "unreachable"
            status["status"] = "degraded"

        try:
            rd_cnf = RedisDBConfig()
            with Redis(**rd_cnf.redis_dict_main, socket_timeout=5) as client:
                client.ping()

        except Exception as e:
            log_etl.info("ETL_API: Status: FAIL")
            LogException(e, logger=log_etl)
            status["redis"] = "unreachable"
            status["status"] = "degraded"

        try:
            fd_cnf = FalkorDBConfig()
            fdb = FalkorDB(**fd_cnf.conn_dict, socket_timeout=5)
            graph = fdb.select_graph(fd_cnf.fdb_kg)
            graph.query("RETURN 1")

        except Exception as e:
            log_etl.info("ETL_API: Status: FAIL")
            LogException(e, logger=log_etl)
            status["falkor"] = "unreachable"
            status["status"] = "degraded"

        return status

    def _status_check(self, task: TaskType, task_id: str):
        try:
            entry = self.tasks[task]
            _status = StatusMessage(
                status=entry.status,
                task=task,
                task_id=task_id,
                message="all ok",
            )

            if entry.task_id != task_id:
                _status.status = TaskStatus.ERROR
                _status.message = "Wrong task_id"

        except Exception as e:
            LogException(e, logger=log_etl)
            _status.status = TaskStatus.ERROR
            _status.message = f"Unknown error: {str(e)}"

        return _status.model_dump()

    def _kill_switch(self, task: TaskType, task_id: str):
        try:
            entry = self.tasks[task]
            _status = StatusMessage(
                status=entry.status,
                task=task,
                task_id=task_id,
                message="all ok",
            )

            # Check for wrong task_id
            if entry.task_id != task_id:
                log_etl.info(
                    f"ETL_API: Failed to kill '{task}: {task_id}' as it is wrong task_id (status: {entry.status.value})"
                )
                _status.status = TaskStatus.ERROR
                _status.message = "Wrong task_id"

            # check for task status
            elif entry.status != TaskStatus.ONGOING:
                log_etl.info(
                    f"ETL_API: Failed to kill '{task}: {task_id}' as it is not running (status: {entry.status.value})"
                )
                _status.status = TaskStatus.ERROR
                _status.message = "Task isn't running"

            # check for process
            elif not entry.process or not entry.process.is_alive():
                log_etl.info(
                    f"ETL_API: Failed to kill '{task}: {task_id}' as process is not present (status: {entry.status.value})"
                )
                _status.status = TaskStatus.ERROR
                _status.message = "Program is missing"

            else:
                # Force kill if still alive
                if entry.process.is_alive():
                    log_etl.info(f"ETL_API: Sending SIGKILL to kill task '{task_id}'")
                    os.killpg(os.getpgid(entry.process.pid), SIGKILL)

                entry.status = TaskStatus.KILLED
                entry.process = None
                _status.status = TaskStatus.KILLED
                _status.message = "Successfully killed task"
                log_etl.info(f"ETL_API: Successfully killed task '{task_id}'")

        except Exception as e:
            LogException(e, logger=log_etl)
            _status.status = TaskStatus.ERROR
            _status.message = f"Unknown error: {str(e)}"

        return _status.model_dump()
