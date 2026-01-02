import json
import random
import asyncio
from datetime import datetime
from aiolimiter import AsyncLimiter
from typing import List, Dict, AsyncGenerator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from camoufox.utils import launch_options
from camoufox.async_api import AsyncCamoufox


class CityRestaurantCrawler:
    def __init__(
        self,
        max_cities: int = 4,
        max_concurrent_per_city: int = 8,
        rate_limit_range: tuple = (2, 5),
        max_retries: int = 3,
        batch_size: int = 10,
        # config,
    ):