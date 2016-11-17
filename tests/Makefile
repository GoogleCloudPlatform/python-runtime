.PHONY: structure-tests
structure-tests:
	make -C no-virtualenv
	make -C virtualenv
	make -C python2-libraries
	make -C python3-libraries

.PHONY: benchmarks
benchmarks:
	make -C benchmark all

.PHONY: google-cloud-python
google-cloud-python:
	make -C google-cloud-python all
