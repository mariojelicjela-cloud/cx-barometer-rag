from typing import Any, Callable


class FastAPI:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def get(self, path: str) -> Callable[..., Any]: ...

    def post(self, path: str) -> Callable[..., Any]: ...

