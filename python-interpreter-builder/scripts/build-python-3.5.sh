#!/bin/bash

set -euo pipefail

# Get the source
mkdir -p /opt/sources
cd /opt/sources
wget --no-verbose https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
shasum --check <<EOF
1524b840e42cf3b909e8f8df67c1724012c7dc7f9d076d4feef2d3eff031e8a0  Python-3.5.2.tgz
EOF
tar xzf Python-3.5.2.tgz

# Build
cd Python-3.5.2

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
# --with-system-expat
#   (Debian) for compatibility with other Debian packages
# --with-system-ffi
#   (Debian) for compatibility with other Debian packages
# --with-system-libmpdec
#   (Debian) for compatibility with other Debian packages
# CFLAGS=-fdebug-prefix-map
#   Unnecessary in our build environment
#
#
# Flags that we _do_ use:
# (Debian) means it was taken from Debian build rules.
#
# --build
#   (Debian)
# --enable-ipv6
#   (Debian)
# --enable-loadable-sqlite-extensions
#   (Debian)
# --enable-optimizations
#   Performance optimization (Enables PGO and may or may not enable
#   LTO based on complex logic and bugs)
# --host
#   (Debian)
# --prefix
#   Avoid possible collisions with Debian or others
# --with-computed-gotos
#   (Debian) Performance optimization
# --with-dbmliborder=bdb:gdbm
#   (Debian) Python default is "ndbm:gdbm:bdb", I have no idea why one
#   would prefer one over the other.
# --with-fpectl
#   (Debian) Floating point exception control
# AR=
#   (Debian) No-op
# CC=
#   (Debian) No-op
# CFLAGS=-fstack-protector-strong
#   (Debian) Security hardening
# CFLAGS=-g
#   (Debian) More debug info
# CFLAGS=-O2
#   (Debian) the default is -O3, don't know why the difference
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
# There is a --with-lto flag, but Debian doesn't use it.  We used to
# use it, but it caused trouble with the uWGSI module.  Instead, we
# pass lto related flags in EXTRA_CFLAGS (to make, rather than
# configure), as Debian does.
#
#
# Debugging: It is very helpful to view and diff sysconfig data from two
# python interpreters.  For example:
#     docker run -it --entrypoint=/opt/python3.5/bin/python3.5 google/python/interpreter-builder -c 'import sysconfig;print("\n".join("%s:%s"%(key,value) for key,value in sorted(sysconfig.get_config_vars().items())))'

mkdir build
cd build
../configure \
  --build=x86_64-pc-linux-gnu\
  --enable-ipv6 \
  --enable-loadable-sqlite-extensions \
  --enable-optimizations \
  --host=x86_64-pc-linux-gnu \
  --prefix=/opt/python3.5 \
  --with-dbmliborder=bdb:gdbm \
  --with-computed-gotos \
  --with-fpectl \
  AR="x86_64-linux-gnu-gcc-ar" \
  CC="x86_64-linux-gnu-gcc" \
  CFLAGS="\
    -fstack-protector-strong \
    -g \
    -O2 \
    -Wformat -Werror=format-security \
  " \
  CPPFLAGS="\
    -D_FORTIFY_SOURCE=2 \
    -Wdate-time \
  " \
  CXX="x86_64-linux-gnu-g++" \
  LDFLAGS="-Wl,-z,relro" \
  RANLIB="x86_64-linux-gnu-gcc-ranlib" \

# Explicitly build the profile-guided-optimized interpreter
EXTRA_OPT_CFLAGS="-g -flto -fuse-linker-plugin -ffat-lto-objects"
NUM_JOBS=$(nproc)
make -j"$NUM_JOBS" EXTRA_CFLAGS="${EXTRA_OPT_CFLAGS}" profile-opt
make -j"$NUM_JOBS" EXTRA_CFLAGS="${EXTRA_OPT_CFLAGS}" test
make altinstall

# Clean-up sources
cd /
rm /opt/sources/Python-3.5.2.tgz
rm -r /opt/sources/Python-3.5.2
