{pkgs, ...}: {
  # https://devenv.sh/languages/
  languages.nix.enable = true;
  languages.python.enable = true;

  # https://devenv.sh/packages/
  packages = with pkgs; [
    # dev
    alejandra
    ruff
    python3Packages.black
    python3Packages.charset-normalizer
    python3Packages.certifi
    python3Packages.click
    python3Packages.coverage
    python3Packages.faker
    python3Packages.idna
    python3Packages.jinja2
    python3Packages.markupsafe
    python3Packages.mock
    python3Packages.netaddr
    python3Packages.pylama
    python3Packages.py
    python3Packages.pytest
    python3Packages.pytest-parallel
    python3Packages.pytestcov
    python3Packages.python-dateutil
    python3Packages.python-lsp-server
    python3Packages.requests
    python3Packages.setuptools
    python3Packages.six
    python3Packages.tblib
    python3Packages.tox
    python3Packages.urllib3
  ];

  pre-commit = {
    # https://devenv.sh/pre-commit-hooks/
    hooks = {
      alejandra.enable = true;
      black.enable = true;
      hadolint.enable = false;
      markdownlint.enable = true;
      prettier.enable = true;
      pylama = {
        enable = true;
        name = "pylama";
        entry = "${pkgs.python3Packages.pylama}/bin/pylama";
        types = ["python"];
      };
      ruff.enable = true;
    };
    settings.markdownlint.config = {
      default = true;
      MD013 = false;
    };
  };

  # See full reference at https://devenv.sh/reference/options/
}
