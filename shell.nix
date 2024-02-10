{ nixpkgs ? import <nixpkgs> { }, system ? builtins.currentSystem }:
let
  devshellSrc = fetchTarball {
    url = "https://github.com/numtide/devshell/archive/f55e05c6d3bbe9acc7363bc8fc739518b2f02976.tar.gz";
    sha256 = "0fv6jgwrcm04q224hd19inlvwaagp86175jykjdrsm7dh3gz0xp7";
  };
  devshell = import devshellSrc { inherit system nixpkgs; };
in
devshell.mkShell {
  name = "django-extra-checks";
  packages = [
    nixpkgs.python312
  ];

  env = [
    {
      name = "PYTHONUNBUFFERED";
      value = "1";
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
      command = "pytest $@";
    }
    {
      help = "install dev deps";
      name = "app.install";
      command = "pip install -U pip wheel && pip install -e .[dev,test] && pre-commit install";
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
