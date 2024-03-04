let _pkgs = import <nixpkgs> { };
in { pkgs ? import (_pkgs.fetchFromGitHub {
  owner = "NixOS";
  repo = "nixpkgs-channels";
  #branch@date: nixpkgs-unstable@2024-02-28
  rev = "d53c2037394da6fe98decca417fc8fda64bf2443";
  sha256 = "02kzypd607zck8xz8x41imw1xmz3v95h1xyjc5dnkz56qn0r5k2f";
}) { } }:

with pkgs;
with python3Packages;

let
  pytest-parallel = buildPythonPackage rec {
    pname = "pytest-parallel";
    version = "0.1.0";

    src = fetchPypi {
      inherit pname version;
      sha256 = "083c8ribi56w8022gvbizcbp0wfrzwslvs0xwm8qpjash3xshqs6";
    };

    propagatedBuildInputs = [ pytest tblib ];

    # There are no tests
    doCheck = false;
  };

  pyPackages = [
    black
    click
    faker
    jinja2
    mock
    netaddr
    pylama
    pytest
    pytest-parallel
    requests
    setuptools
    tox
  ];

in mkShell { buildInputs = [ python3 ] ++ pyPackages; }
