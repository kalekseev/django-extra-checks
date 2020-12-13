from typing import Any, Dict, Iterable, Optional, Tuple

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol

from django.db import models


class ArgASTProtocol(Protocol):
    @property
    def is_callable(self) -> bool:
        ...

    @property
    def callable_func_name(self) -> Optional[str]:
        ...

    def get_call_first_args(self) -> Any:
        ...


class FieldASTProtocol(Protocol):
    def get_arg(self, name: str) -> Optional[ArgASTProtocol]:
        ...


class ModelASTProtocol(Protocol):
    @property
    def field_nodes(self) -> Iterable[Tuple[models.fields.Field, FieldASTProtocol]]:
        ...

    def has_meta_var(self, name: str) -> bool:
        return name in self._meta_vars

    @property
    def _meta_vars(self) -> Dict[str, Any]:
        ...
