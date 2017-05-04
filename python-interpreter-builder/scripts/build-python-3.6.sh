#!/bin/bash

set -euo pipefail
set -x

# Get the source
mkdir -p /opt/sources
cd /opt/sources
wget --no-verbose https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz
# SHA-256 generated via `shasum -a 256 [file]`
shasum --check <<EOF
aa50b0143df7c89ce91be020fe41382613a817354b33acdc6641b44f8ced3828  Python-3.6.1.tgz
EOF
tar xzf Python-3.6.1.tgz

# Build
cd Python-3.6.1

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

mkdir build-static
cd build-static

../configure \
  --enable-ipv6 \
  --enable-loadable-sqlite-extensions \
  --enable-optimizations \
  --prefix=/opt/python3.6 \
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

# Due to https://bugs.python.org/issue29243, "make altinstall"
# rebuilds everything from scratch, twice.  This is a workaround.
sed -i 's/^all:.*$/all: build_all/' Makefile

make profile-opt
make altinstall

# Clean-up sources
cd /opt
rm /opt/sources/Python-3.6.1.tgz
rm -r /opt/sources/Python-3.6.1
