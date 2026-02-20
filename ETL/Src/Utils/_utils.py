import os
import re
from datetime import timedelta, timezone
from typing import Any

from dotenv import load_dotenv


class util_func:
    @staticmethod
    def get_timezone() -> timezone:
        """Method to get timezone information from environment variables"""
        TZ = timezone(timedelta(hours=5, minutes=30))
        try:
            load_dotenv(".env")
            hrs, min = os.getenv("TIMEZONE", "5:30").split(":")
            TZ = timezone(timedelta(hours=int(hrs), minutes=int(min)))

        except Exception:
            pass  # fallback to default IST

        return TZ

    @staticmethod
    def get_seeder_info() -> list[Any]:
        """Method to get Seeder function parameters from environment variables"""
        from .exception import LogException
        from .logger import log_etl

        try:
            load_dotenv(".env")
            website, pattern, headers, threads = [
                os.getenv(item, "")
                for item in [
                    "SEEDER_WEBSITE",
                    "SEEDER_PATTERN",
                    "SEEDER_HEADERS",
                    "SEEDER_THREADS",
                ]
            ]
            log_etl.info("Seeder: Got seeder ENV Vars")

        except Exception as e:
            LogException(e, logger=log_etl)

        return (website, re.compile(pattern), headers, int(threads), 10)

    @staticmethod
    def format_time(seconds: float) -> str:
        """Format elapsed time as '00 hr, 00 min, 00 sec'

        Arguments:
            seconds (float): Time to format

        Returns:
            time (str): Time formatted as a string
        """
        hrs, rem = divmod(seconds, 3600)
        mins, secs = divmod(rem, 60)
        return f"{int(hrs):2d} hr, {int(mins):2d} min, {int(secs):2d} sec"
