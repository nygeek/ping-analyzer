#
# analyze_pings development sandbox
#

DIRS = "."
DIRPATH="~/projects/p/pinger"

BUILD_VERSION := $(shell cat version.txt)

HOSTS = waffle pancake
PUSH_FILES = $(HOSTS:%=.%_push)

help: ${FORCE}
	cat Makefile

SOURCE = \
	analyze_pings.py \
	LICENSE.md \
	LineQueue.py \
	Makefile \
	README.md

DATA = \
	data/sample.txt \
	data/2017-11-26-15.38.txt

FILES = \
	${SOURCE} \
	lqtest.txt

stuff.tar: ${FORCE}
	tar -cvf stuff.tar ${FILES}

DATA = sample.txt

CRUNCHER = analyze_pings.py

test: ${FORCE}
	head -100000 ${DATA} > ${HOME}/tmp/test.txt
	python ${CRUNCHER} -v ${BUILD_VERSION} -f ${HOME}/tmp/test.txt

run: ${FORCE}
	python ${CRUNCHER} -v ${BUILD_VERSION} -f ${DATA}

lqtest: ${FORCE}
	python LineQueue.py

# Quality management

pylint: ${SOURCE}
	pylint ${SOURCE}

# GIT operations

diff: .gitattributes
	git diff

commit: .gitattributes
	git commit ${FILES}
	git describe --abbrev=4 --dirty --always --tags > version.txt

version.txt: ${FORCE}
	git describe --abbrev=4 --dirty --always --tags > version.txt

log: .gitattributes
	git log --pretty=oneline

# Distribution to other hosts

push: ${PUSH_FILES}
	rm ${PUSH_FILES}

.%_push:
	rsync -az --exclude=".git*" --exclude=".*_push" -e ssh ${DIRS} $*:${DIRPATH}
	touch $@

FORCE: 
