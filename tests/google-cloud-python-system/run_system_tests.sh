#!/bin/sh
set -eu

cd /app/google-cloud-python

# Not all packages have system tests
packages="
bigquery
bigtable
datastore
language
logging
monitoring
pubsub
spanner
speech
storage
vision
"

# translate has system test but it gives error message:
#  BadRequest: 400 Invalid JSON payload received. Unknown name "model": Cannot bind 'nmt'. Field 'model' could not be found in request message. (GET https://translation.googleapis.com/language/translate/v2?target=de&q=hvala+ti&q=dankon&q=Me+llamo+Jeff&q=My+name+is+Jeff&model=nmt)
disabled_packages="translate"

# Spanner system test needs this
export GOOGLE_CLOUD_TESTS_CREATE_SPANNER_INSTANCE=1

exit_code=0
for package in ${packages}; do
  noxfile="${package}/nox.py"
  nox \
    -f "${noxfile}" \
    -e \
    "system(py='2.7')" \
    "system(py='3.6')" \
    || exit_code=1
done

exit "${exit_code}"
