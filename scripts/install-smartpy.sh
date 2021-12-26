#!/usr/bin/env bash

set -euo pipefail

usage () {
    >&2 cat <<EOF
Usage: $(basename $0) <options>

The options are as follows:

--prefix <prefix>
        Install into directory <prefix>.

--from <url>
        Fetch the installation files from <url>. May be of the form 'file:///path/to/files/'.

--with-smartml
        Also install SmartML.

--native
        Install native binaries (experimental).

--yes
        Answer 'y' to all questions during installation.

--help

EOF
exit
}

prefix=~/smartpy-cli
from=https://smartpy.io/cli
with_smartml=false
native=false
yes=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prefix)
            prefix="$2"
            shift 2
            ;;
        --from)
            from="$2"
            shift 2
            ;;
        --with-smartml)
            with_smartml=true
            shift
            ;;
        --native)
            native=true
            shift
            ;;
        --yes)
            yes=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            >&2 echo Unexpected argument: "$1"
            exit 1
            ;;
    esac
done


>&2 echo -n "Install into $prefix? [y/N] "
if [ "$yes" == "true" ]; then
    >&2 echo "y"
else
    read ok
    if [ "$ok" != "y" ]; then
        >&2 echo "Installation aborted."
        exit 1
    fi
fi

if [ -d "$prefix" ]; then
    >&2 echo -n "The directory $prefix exists. Delete and replace? [y/N] "
    if [ "$yes" == "true" ]; then
        >&2 echo "y"
    else
        read ok
        if [ "$ok" != "y" ]; then
            >&2 echo "Installation aborted."
            exit 1
        fi
    fi
    rm -rf "$prefix"
fi

if [ -e "$prefix" ]; then
    >&2 echo "$prefix exists, but is not a directory."
    exit 1
fi

mkdir -p "$prefix"

>&2 echo "Downloading files..."
curl "$from"/smartpy-cli.tar.gz | tar xzf - -C "$prefix"
if [ "$native" != true ]; then
    rm -f "$prefix/smartpyc"
fi

>&2 echo "Installing npm packages..."
cd "$prefix"
npm --loglevel silent --ignore-scripts init --yes > /dev/null
npm --loglevel silent --ignore-scripts install libsodium-wrappers-sumo bs58check js-sha3 tezos-bls12-381 chalk @smartpy/originator @smartpy/timelock
cd -

if [ "$with_smartml" == "true" ]; then
    >&2 echo "Downloading SmartML files..."
    curl "$from"/smartML.tar.gz | tar xzf - -C "$prefix"

    if [ "$native" != "true" ]; then
        rm -f "$prefix/smartpyc"
    fi

    >&2 echo "Setting up SmartML..."
    cd "$prefix"
    set -x
    opam switch create . ocaml-base-compiler.4.10.2
    opam switch import env/switch.export
    opam install -y \
      ocamlfind \
      smartML/utils_pure/utils_pure.opam \
      smartML/ppx_smartml/ppx_smartml_lib.opam \
      smartML/ppx_smartml/driver.opam
    ocamlfind ocamlmktop -o smarttop.exe -package num,utils_pure,smartML -linkpkg
    ln -s _opam/bin/driver driver.exe
    chmod +x smarttop smarttop.exe
    set +x
    cd -
fi

>&2 echo "Installation successful in $prefix."
