{ pkgs ? import <nixpkgs> { }, system ? builtins.currentSystem }:
with pkgs;
let
  src = fetchTarball {
    url = "https://github.com/numtide/devshell/archive/f64db97388dda7c2c6f8fb7aa5d6d08365fb1e01.tar.gz";
    sha256 = "1421h6bhsg4fishz10092m71qnd5ll6129l45kychzh9kp23040s";
  };
  devshell = import src { inherit system; };
in
devshell.mkShell {
  name = "django-extra-checks";
  packages = [
    python38Full
  ];

  env = [
    {
      name = "PYTHONUNBUFFERED";
      value = "1";
    }
    {
      name = "PYTHONPATH";
      eval = "$PWD";
    }
    {
      name = "DJANGO_SETTINGS_MODULE";
      value = "tests.settings";
    }
  ];

  commands = [
    {
      help = "run tests";
      name = "app.test";
      command = "pytest";
    }
    {
      help = "install dev deps";
      name = "app.install";
      command = "pip install -U pip wheel && pip install -e .[dev] && pre-commit install";
    }
    {
      help = "typecheck project";
      name = "app.typecheck";
      command = "mypy src/extra_checks tests";
    }
    {
      help = "lint project";
      name = "app.lint";
      command = "pre-commit run -a";
    }
    {
      help = "run main tox env";
      name = "app.tox";
      command = ''
        unset PYTHONPATH;
        tox -e 'py{38}-django{22,30,31,32,32-drf,-latest},flake8,black,isort,manifest,mypy,check'
      '';
    }
  ];
}
