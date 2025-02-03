import inspect
import re
import textwrap
from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from extra_checks.check_id import ALL_CHECKS_NAMES, CheckId

if TYPE_CHECKING:
    cached_property = property
else:
    from django.utils.functional import cached_property


DISABLE_COMMENT_PATTERN = r"^#\s*extra-checks-disable-next-line(?:\s+(.*))?$"


def _parse_comment(checks: Optional[str]) -> set[str]:
    if not checks:
        return ALL_CHECKS_NAMES  # type: ignore
    result = set()
    for scheck in checks.split(","):
        check = CheckId.find_check(scheck.strip())
        if check:
            result.add(check.value)
    return result


def _find_disabled_checks(comments: Iterable[str]) -> set[str]:
    result = set()
    for line in comments:
        m = re.match(DISABLE_COMMENT_PATTERN, line)
        if m:
            result |= _parse_comment(m.groups()[0])
    return result


class SourceProvider:
    def __init__(self, obj: type) -> None:
        self._obj = obj
        self._comments_cache: dict[int, set[str]] = {}

    @cached_property
    def source(self) -> Optional[str]:
        try:
            return textwrap.dedent(inspect.getsource(self._obj))
        except (TypeError, OSError):
            # TODO: add warning?
            return None

    @cached_property
    def _top_comments(self) -> Iterable[str]:
        for line in (inspect.getcomments(self._obj) or "").splitlines()[::-1]:
            yield line.strip()

    def _get_line_comments(self, line_no: int) -> Iterable[str]:
        line_no -= 2
        if line_no < 0:
            yield from self._top_comments
        for line in (self.source or "").splitlines()[line_no::-1]:
            sline = line.strip()
            if sline.startswith("#"):
                yield sline
            else:
                break

    def get_disabled_checks_for_line(self, line_no: int) -> set[str]:
        if line_no not in self._comments_cache:
            comments = self._get_line_comments(line_no)
            self._comments_cache[line_no] = _find_disabled_checks(comments)
        return self._comments_cache[line_no]
