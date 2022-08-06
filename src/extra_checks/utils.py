from typing import Iterable, Iterator, Optional, Set, Type, TypeVar

TBase = TypeVar("TBase")


def collect_subclasses(
    bases: Iterable[Type[TBase]],
    visited: Optional[Set[Type[TBase]]] = None,
) -> Iterator[Type[TBase]]:
    visited = visited or set()
    for cls in bases:
        if cls not in visited:
            visited.add(cls)
            yield from collect_subclasses(cls.__subclasses__(), visited)
            yield cls
