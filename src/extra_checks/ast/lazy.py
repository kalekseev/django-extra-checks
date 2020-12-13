from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

from django.db import models

from .exceptions import MissingASTError
from .protocols import FieldASTProtocol

if TYPE_CHECKING:
    from .ast import FieldAST
    from .cst import FieldCST


class LazyFieldAST:
    def __init__(
        self,
        field_ast_class: Union[Type["FieldAST"], Type["FieldCST"]],
        assignments: Dict[str, Any],
        field: models.Field,
    ) -> None:
        self.assignments = assignments
        self.field = field
        self.field_ast: Optional[FieldASTProtocol] = None
        self.field_ast_class = field_ast_class

    def __getattr__(self, name: str) -> Any:
        if not self.field_ast:
            try:
                self.field_ast = self.field_ast_class(
                    self.assignments[self.field.name], self.field
                )
            except KeyError:
                raise MissingASTError()
        return getattr(self.field_ast, name)
