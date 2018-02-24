#!/bin/sh
set -eu

cd /app/google-cloud-python

exit_code=0
failed_files=
for noxfile in */nox.py; do
  if [ "${noxfile}" = "dlp/nox.py" ]; then
    echo "**** Skipping ${noxfile} ****"
    continue
  fi
  echo "**** Starting tests in ${noxfile} ****"
  nox \
    -f "${noxfile}" \
    -e \
    "unit(py='2.7')" \
    "unit(py='3.4')" \
    "unit(py='3.5')" \
    "unit(py='3.6')" \
    || {
      echo "**** FAILED tests in ${noxfile} ****"
      exit_code=1
      failed_files="${failed_files} ${noxfile}"
    }
  echo "**** Finished tests in ${noxfile} ****"
done

if [ "${exit_code}" -eq 0 ]; then
  echo "**** All tests passed ****"
else
  echo "**** There were test failures:${failed_files} ****"
fi
exit "${exit_code}"
