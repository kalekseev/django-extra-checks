{ pkgs ? import <nixpkgs> { }, system ? builtins.currentSystem }:
with pkgs;
let
  devshellSrc = fetchTarball {
    url = "https://github.com/numtide/devshell/archive/f87fb932740abe1c1b46f6edd8a36ade17881666.tar.gz";
    sha256 = "10cimkql88h7jfjli89i8my8j5la91zm4c78djqlk22dqrxmm6bs";
  };
  devshell = import devshellSrc { inherit system pkgs; };
in
devshell.mkShell {
  name = "django-extra-checks";
  packages = [
    python310
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
  ];
}
