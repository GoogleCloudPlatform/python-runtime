#!/bin/bash

set -euo pipefail
set -x

# Get the source
mkdir -p /opt/sources
cd /opt/sources
wget --no-verbose https://www.python.org/ftp/python/3.5.9/Python-3.5.9.tgz
# SHA-256 generated via `shasum -a 256 [file]`
shasum --check <<EOF
67a1d4fc6e4540d6a092cadc488e533afa961b3c9becc74dc3d6b55cb56e0cc1  Python-3.5.9.tgz
EOF
tar xzf Python-3.5.9.tgz

cd Python-3.5.9

# Explanation of flags:
#
# Noteworthy Debian options we _don't_ use:
#
# --enable-shared
#   This is complicated to get right, and we don't expect our
#   customers to embed Python in a native code application.  There is
#   also a noteworthy interaction with 'make altinstall'
#   (https://bugs.python.org/issue27685)
# --without-ensurepip
#   Debian unbundles pip for their own reasons
# CFLAGS=-fdebug-prefix-map
#   Unnecessary in our build environment
#
#
# Flags that we _do_ use:
# (Debian) means it was taken from Debian build rules.
#
# --enable-ipv6
#   (Debian) Ensure support is compiled in instead of relying on autodetection
# --enable-loadable-sqlite-extensions
#   (Debian)
# --enable-optimizations
#   Performance optimization (Enables PGO and may or may not enable
#   LTO based on complex logic and bugs)
# --prefix
#   Avoid possible collisions with Debian or others
# --with-computed-gotos
#   (Debian) Performance optimization
# --with-dbmliborder=bdb:gdbm
#   (Debian) Python default is "ndbm:gdbm:bdb", I have no idea why one
#   would prefer one over the other.
# --with-fpectl
#   (Debian) Floating point exception control
# --with-system-expat
#   (Debian) for compatibility with other Debian packages
# --with-system-ffi
#   (Debian) for compatibility with other Debian packages
# --with-system-libmpdec
#   (Debian) for compatibility with other Debian packages
# AR=
#   (Debian) No-op
# CC=
#   (Debian) No-op
# CFLAGS=-fstack-protector-strong
#   (Debian) Security hardening
# CFLAGS=-g
#   (Debian) More debug info
# CFLAGS=-Wformat -Werror=format-security
#   (Debian) Security hardening
# CPPFLAGS=-D_FORTIFY_SOURCE=2
#   (Debian) Security hardening
# CPPFLAGS=-Wdate-time
#   (Debian) Warnings about non-reproducible builds
# CXX=
#   (Debian) No-op
# LDFLAGS=-Wl,-z,relro:
#   (Debian) Security hardening
# RANLIB=
#   (Debian) No-op
#
#
# LTO (Link time optimization)
#
# Currently disabled, due to unresolved compile problems.  There is a
# --with-lto flag, but Debian doesn't use it.  Instead, they pass lto
# related flags in EXTRA_CFLAGS (to make, rather than configure).
# Specifically EXTRA_CFLAGS="-g -flto -fuse-linker-plugin
# -ffat-lto-objects"

PREFIX=/opt/python3.5

mkdir build-static
cd build-static

../configure \
  --enable-ipv6 \
  --enable-loadable-sqlite-extensions \
  --enable-optimizations \
  --prefix="$PREFIX" \
  --with-dbmliborder=bdb:gdbm \
  --with-computed-gotos \
  --with-fpectl \
  --with-system-expat \
  --with-system-ffi \
  --with-system-libmpdec \
  AR="x86_64-linux-gnu-gcc-ar" \
  CC="x86_64-linux-gnu-gcc" \
  CFLAGS="\
    -fstack-protector-strong \
    -g \
    -Wformat -Werror=format-security \
  " \
  CPPFLAGS="\
    -D_FORTIFY_SOURCE=2 \
    -Wdate-time \
  " \
  CXX="x86_64-linux-gnu-g++" \
  LDFLAGS="-Wl,-z,relro" \
  RANLIB="x86_64-linux-gnu-gcc-ranlib" \

make profile-opt

# Run tests
# test___all__: Depends on Debian-specific locale changes
# test_dbm: https://bugs.python.org/issue28700
# test_imap: https://bugs.python.org/issue30175
# test_shutil: https://bugs.python.org/issue29317
# test_xmlrpc_net: https://bugs.python.org/issue31724
make test TESTOPTS="--exclude test___all__ test_dbm test_imaplib test_shutil test_xmlrpc_net"

# Install
make altinstall
# Remove redundant copy of libpython
rm "$PREFIX"/lib/libpython3.5m.a
# Remove opt-mode bytecode
find "$PREFIX"/lib/python3.5/ \
  -name \*.opt-\?.pyc \
  -exec rm {} \;
# Remove all but a few files in the 'test' subdirectory
find "$PREFIX"/lib/python3.5/test \
  -mindepth 1 -maxdepth 1 \
  \! -name support \
  -a \! -name __init__.py \
  -a \! -name pystone.\* \
  -a \! -name regrtest.\* \
  -a \! -name test_support.py \
  -exec rm -rf {} \;

# Clean-up sources
cd /opt
rm /opt/sources/Python-3.5.9.tgz
rm -r /opt/sources/Python-3.5.9

# Archive and copy to persistent external volume
tar czf /workspace/runtime-image/interpreter-3.5.tar.gz /opt/python3.5
