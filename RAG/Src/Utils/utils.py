from typing import List


class prompt_func:
    @staticmethod
    def read(path: str, chunk: bool = False) -> str | List[str]:
        """Method to read prompt data

        Args:
            path (str): Path to prompt .txt file

        Returns:
            data (str | List[str]): Prompt text as a string or list of string
        """
        from .exception import LogException
        from .logger import log_rag

        try:
            with open(path, mode="rt", encoding="utf-8", newline="\r\n") as f:
                data = f.read()
            data = (
                [part.strip() for part in data.split("\n\n") if part.strip()]
                if chunk
                else data
            )
            log_rag.info("Successfully read prompt text from file")

        except Exception as e:
            LogException(e, logger=log_rag)

        return data


class cypher_func:
    @staticmethod
    def read(path: str, chunk: bool = False) -> str | List[str]:
        """Method to read cypher code

        Args:
            path (str): Path to cypher .cyp file

        Returns:
            data (str | List[str]): Cypher code as a string or list of string
        """
        from .exception import LogException
        from .logger import log_rag

        try:
            with open(path, mode="rt", encoding="utf-8", newline="\r\n") as f:
                data = f.read()
            data = (
                [part.strip() for part in data.split("\n\n") if part.strip()]
                if chunk
                else data
            )
            log_rag.info("Successfully read prompt text from file")

        except Exception as e:
            LogException(e, logger=log_rag)

        return data
