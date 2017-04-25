#!/bin/bash

set -euo pipefail

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
# CFLAGS=-specs=/usr/share/dpkg/no-pie-link.specs
#   (Debian) Temporarily disable security hardening
# CFLAGS=-Wformat -Werror=format-security
#   (Debian) Security hardening
# CPPFLAGS=-D_FORTIFY_SOURCE=2
#   (Debian) Security hardening
# CPPFLAGS=-Wdate-time
#   (Debian) Warnings about non-reproducible builds
# CXX=
#   (Debian) No-op
# LDFLAGS=-specs=/usr/share/dpkg/no-pie-link.specs
#   (Debian) Temporarily disable security hardening
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
#     docker run -it --entrypoint=/opt/python3.6/bin/python3.6 google/python/interpreter-builder -c 'import sysconfig;print("\n".join("%s:%s"%(key,value) for key,value in sorted(sysconfig.get_config_vars().items())))'

mkdir build-static
cd build-static

../configure \
  --build=x86_64-pc-linux-gnu \
  --enable-ipv6 \
  --enable-loadable-sqlite-extensions \
  --enable-optimizations \
  --host=x86_64-pc-linux-gnu \
  --prefix=/opt/python3.6 \
  --with-dbmliborder=bdb:gdbm \
  --with-computed-gotos \
  --with-fpectl \
  AR="x86_64-linux-gnu-gcc-ar" \
  CC="x86_64-linux-gnu-gcc" \
  CFLAGS="\
    -fstack-protector-strong \
    -g \
    -specs=/usr/share/dpkg/no-pie-compile.specs \
    -Wformat -Werror=format-security \
  " \
  CPPFLAGS="\
    -D_FORTIFY_SOURCE=2 \
    -Wdate-time \
  " \
  CXX="x86_64-linux-gnu-g++" \
  LDFLAGS="\
    -specs=/usr/share/dpkg/no-pie-link.specs \
    -Wl,-z,relro \
  " \
  RANLIB="x86_64-linux-gnu-gcc-ranlib" \

# Explicitly build the profile-guided-optimized interpreter
NUM_JOBS="$(nproc)"
make \
  -j"${NUM_JOBS}" \
  EXTRA_CFLAGS="" \
  PROFILE_TASK="../Lib/test/regrtest.py -s -j 1 -unone,decimal -x test_cmd_line_script test_compiler test_concurrent_futures test_ctypes test_dbm_dumb test_dbm_ndbm test_distutils test_ensurepip test_gdb test_ioctl test_linuxaudiodev test_multiprocessing test_ossaudiodev test_pydoc test_signal test_socket test_socketserver test_subprocess test_sundry test_thread test_threaded_import test_threadedtempfile test_threading test_threading_local test_threadsignals test_venv test_zipimport_support" \
  profile-opt

make altinstall

# Clean-up sources
cd /opt
rm /opt/sources/Python-3.6.1.tgz
rm -r /opt/sources/Python-3.6.1
