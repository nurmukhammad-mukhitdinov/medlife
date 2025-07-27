import inspect

from fastapi.exceptions import HTTPException
from loguru import logger


class LoggedHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


def raise_with_log(status_code: int, detail: str) -> None:
    """Wrapper function for logging and raising exceptions."""

    desc = f"<HTTPException status_code={status_code} detail={detail}>"
    # if status_code == 404:
    #     logger.debug(f"{desc} | runner={runner_info()}")
    # else:
    logger.error(f"{desc} | runner={runner_info()}")
    raise LoggedHTTPException(status_code, detail)


def runner_info() -> str:
    info = inspect.getframeinfo(inspect.stack()[2][0])
    return f"{info.filename}:{info.function}:{info.lineno}"
