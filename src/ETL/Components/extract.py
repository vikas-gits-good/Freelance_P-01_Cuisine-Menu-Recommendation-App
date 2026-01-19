from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class Extract:
    def __init__(self) -> None:
        pass

    def run(self):
        try:
            pass

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)
