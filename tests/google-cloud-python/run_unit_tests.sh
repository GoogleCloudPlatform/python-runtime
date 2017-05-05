#!/bin/sh
set -eu

cd /app/google-cloud-python

exit_code=0
for noxfile in */nox.py; do
  nox \
    -f "${noxfile}" \
    -e \
    "unit_tests(python_version='2.7')" \
    "unit_tests(python_version='3.4')" \
    "unit_tests(python_version='3.5')" \
    "unit_tests(python_version='3.6')" \
    || exit_code=1
done

exit "${exit_code}"
