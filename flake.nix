{
  description = "Typing practice in your terminal";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
      in
      {
        packages = {
          default = python.pkgs.buildPythonApplication {
            pname = "desire-typer";
            version = "1.0.0";
            src = ./.;
            format = "pyproject";

            nativeBuildInputs = [ python.pkgs.setuptools ];

            meta = {
              description = "Desire statement typing in your terminal";
              homepage = "https://github.com/pmamico/desire-typer";
              license = pkgs.lib.licenses.mit;
              mainProgram = "typer";
            };
          };
        };

        devShells.default = pkgs.mkShell {
          packages = [
            python
            python.pkgs.setuptools
            python.pkgs.pip
          ];
        };
      }
    );
}
