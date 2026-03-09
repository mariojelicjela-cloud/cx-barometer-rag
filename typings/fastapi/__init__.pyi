from typing import Any, Callable, Dict, Optional


class State:
    def __init__(self) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...


class FastAPI:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    state: State

    def get(self, path: str) -> Callable[..., Any]: ...

    def post(self, path: str) -> Callable[..., Any]: ...


class Request:
    app: FastAPI


class HTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: Any = ...,
        headers: Optional[Dict[str, str]] = ...,
    ) -> None: ...

