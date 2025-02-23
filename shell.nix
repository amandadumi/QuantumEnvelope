# development shell, includes all dependencies, debug, style tools
{
  pkgs ? import <nixpkgs> {}
}:
let 
  callPackage = pkgs.lib.callPackageWith pkgs;
  mnemo-src = pkgs.fetchgit {
    url = "https://github.com/perarnau/mnemo.git";
   # rev = "master";
    branchName = "master";
    sha256 = "0awhb1hmszdx37pf0y8k199mn7nzz31bv8pd61lq0nbm29lmqid7";
  };
  mnemo = callPackage ./nix/mnemo.nix { src = mnemo-src; };
  mnemo-py = callPackage ./nix/mnemo-py.nix { src = mnemo-src; mnemo = mnemo; };
in
with pkgs;
pkgs.mkShell {
        name = "miniqp";
	nativeBuildInputs = [ ];
        buildInputs = [
          # dependencies for the code
          python3
          python3Packages.black
          python3Packages.notebook
          python3Packages.matplotlib
          python3Packages.ipywidgets
          python3Packages.tqdm
          python3Packages.numpy
          python3Packages.mypy
          python3Packages.mpi4py
          python3Packages.mpi4py.mpi
          python3Packages.flake8
          mnemo-py
          pkgconfig
          scalapack
        ];
}
