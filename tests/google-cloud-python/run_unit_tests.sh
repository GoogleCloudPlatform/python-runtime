#!/bin/sh
set -eu

cd /app/google-cloud-python

exit_code=0
for noxfile in */nox.py; do
  nox \
    -f "${noxfile}" \
    -e \
    "unit(py='2.7')" \
    "unit(py='3.4')" \
    "unit(py='3.5')" \
    "unit(py='3.6')" \
    || exit_code=1
done

exit "${exit_code}"
