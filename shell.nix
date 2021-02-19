let _pkgs = import <nixpkgs> { };
in { pkgs ? import (_pkgs.fetchFromGitHub {
  owner = "NixOS";
  repo = "nixpkgs-channels";
  #branch@date: nixpkgs-unstable@2021-01-25
  rev = "4762fba469e2baa82f983b262e2c06ac2fdaae67";
  sha256 = "1sidky93vc2bpnwb8avqlym1p70h2szhkfiam549377v9r5ld2r1";
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
