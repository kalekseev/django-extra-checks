from typing import TYPE_CHECKING, Any, Dict, List

from django.core import checks
from django.core.management.base import SystemCheckError
from django.core.management.commands.check import Command as BaseCommand

if TYPE_CHECKING:
    from extra_checks.checks.base_checks import ExtraCheckMessage


class Command(BaseCommand):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._errors: "List[ExtraCheckMessage]" = []

    def add_arguments(self, parser: Any) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Apply autofix if available.",
        )
        parser.add_argument(
            "--fix-black",
            action="store_true",
            help="Apply black on autofix result.",
        )

    def _run_checks(self, **kwargs: Any) -> dict:
        errors = checks.run_checks(**kwargs)
        self._errors = errors
        return errors

    def handle(self, *app_labels: Any, **options: Any) -> None:
        on_exit = None
        try:
            super().handle(*app_labels, **options)
        except SystemCheckError as exc:
            on_exit = exc
        if not options["fix"]:
            return
        import libcst as cst
        from libcst import matchers as m

        files: Dict[str, List[m.MatcherDecoratableTransformer]] = {}
        for error in self._errors:
            fix = getattr(error, "_fix", None)
            file = getattr(error, "_file", None)
            if fix and file:
                files.setdefault(file, []).append(fix)
        for file, fixes in files.items():
            with open(file, "r") as f:
                source_text = f.read()
            tree = cst.parse_module(source_text)
            for fix in fixes:
                tree = tree.visit(fix)
            result_text = tree.code
            if source_text != result_text:
                if options["fix_black"]:
                    import black

                    mode = black.FileMode()
                    fast = False
                    result_text = black.format_file_contents(
                        src_contents=result_text, fast=fast, mode=mode
                    )
                with open(file, "w") as f:
                    f.write(result_text)
        if on_exit:
            raise on_exit
