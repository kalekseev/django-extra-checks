from collections.abc import Iterable, Iterator
from typing import Optional, TypeVar

TBase = TypeVar("TBase")


def collect_subclasses(
    bases: Iterable[type[TBase]],
    visited: Optional[set[type[TBase]]] = None,
) -> Iterator[type[TBase]]:
    visited = visited or set()
    for cls in bases:
        if cls not in visited:
            visited.add(cls)
            yield from collect_subclasses(cls.__subclasses__(), visited)
            yield cls
