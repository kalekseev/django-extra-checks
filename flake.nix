{
  description = "Django Extra Checks";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        app-test = pkgs.writeShellScriptBin "app.test" ''pytest $@'';
        app-install = pkgs.writeShellScriptBin "app.install" ''uv pip install -e .[dev,test] && pre-commit install'';
        app-typecheck = pkgs.writeShellScriptBin "app.typecheck" ''mypy src/extra_checks tests'';
        app-lint = pkgs.writeShellScriptBin "app.lint" ''pre-commit run -a'';
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python312
            pkgs.pre-commit
          ];
          buildInputs = [
            app-test
            app-install
            app-typecheck
            app-lint
          ];
          shellHook = ''
            export PYTHONUNBUFFERED=1;
            export PYTHONPATH=src;
            export DJANGO_SETTINGS_MODULE=tests.settings;
            export VIRTUAL_ENV="$(pwd)/.venv"
            [[ -d $VIRTUAL_ENV ]] || uv -q venv $VIRTUAL_ENV
            export PATH="$VIRTUAL_ENV/bin":$PATH
          '';
        };
      }
    );
}
