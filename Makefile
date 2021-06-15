#
# analyze_pings development sandbox
#

# 2021-06-15 - change ${FORCE} to .PHONY:
# And get rid of rsync to update other donner.lan hosts.

DIRS = "."
DIRPATH="~/projects/p/pinger"

BUILD_VERSION := $(shell cat version.txt)

HOSTS = waffle pancake
PUSH_FILES = $(HOSTS:%=.%_push)

.PHONY: help
help:
	cat Makefile

SOURCE = \
	analyze_pings.py \
	insert_timestamps.py \
	LICENSE.md \
	LineQueue.py \
	Makefile \
	pinger.py \
	README.md \
	SequenceStats.py \
	TimeStamp.py

# various ping logs
DATA = \
	data/2017-11-26-15.38.txt \
	data/panix.com.ping.log \
	data/sample.txt

# support data
FILES = \
	${SOURCE} \
	.gitignore \
	pinger.cfg \
	lqtest.txt

.PHONY: stuff.tar
stuff.tar:
	tar -cvf stuff.tar ${FILES}

DATA = data/panix.com.ping.log

CRUNCHER = analyze_pings.py

.PHONY: test
test:
	head -100000 ${DATA} > ${HOME}/tmp/test.txt
	python ${CRUNCHER} -v ${BUILD_VERSION} -f ${HOME}/tmp/test.txt

.PHONY: run
run:
	python ${CRUNCHER} -v ${BUILD_VERSION} -f ${DATA}

.PHONY: lqtest
lqtest:
	python LineQueue.py

# Quality management

pylint: ${SOURCE}
	pylint ${SOURCE}

# GIT operations

diff: .gitattributes
	git diff

.PHONY: status
status:
	git status

# this brings the remote copy into sync with the local one
commit: .gitattributes
	git commit ${FILES}
	git push -u origin master
	git describe --abbrev=4 --dirty --always --tags > version.txt

# This brings the local copy into sync with the remote (master)
pull: .gitattributes
	git pull origin master

.PHONY: version.txt
version.txt:
	git describe --abbrev=4 --dirty --always --tags > version.txt

log: .gitattributes
	git log --pretty=oneline
