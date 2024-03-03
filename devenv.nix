{ pkgs, ... }:

{
  packages = [ pkgs.uv ];

  env.PYTHONUNBUFFERED = "1";
  env.PYTHONPATH = "src";
  env.DJANGO_SETTINGS_MODULE = "tests.settings";

  languages.python.enable = true;
  languages.python.package = pkgs.python312;

  scripts."app.test".exec = "pytest $@";
  scripts."app.install".exec = "uv pip install -e .[dev,test] && pre-commit install";
  scripts."app.typecheck".exec = "mypy src/extra_checks tests";
  scripts."app.lint".exec = "pre-commit run -a";
}
