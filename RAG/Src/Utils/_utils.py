import os
from datetime import timedelta, timezone

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
