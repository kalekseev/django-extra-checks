from django.core import checks
from django.core.management.base import SystemCheckError
from django.core.management.commands.check import Command as BaseCommand


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._errors = []

    def add_arguments(self, parser):
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

    def _run_checks(self, **kwargs):
        errors = checks.run_checks(**kwargs)
        self._errors = errors
        return errors

    def handle(self, *app_labels, **options):
        on_exit = None
        try:
            super().handle(*app_labels, **options)
        except SystemCheckError as exc:
            on_exit = exc
        if not options["fix"]:
            return
        import libcst as cst

        files = {}
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
