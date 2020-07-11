with import <nixpkgs> {};
with pkgs.python3Packages;

buildPythonPackage rec {
  name = "autocut";
  src = ./.;
  propagatedBuildInputs = [ numpy librosa nose pkgs.mlt ];
}
