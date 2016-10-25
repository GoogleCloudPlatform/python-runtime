.PHONY: all
all:
	make -C no-virtualenv
	make -C virtualenv
	make -C google-cloud-python
	make -C python2-libraries
	make -C python3-libraries

.PHONY: benchmarks
benchmarks:
	make -C benchmark all
