#
# analyze_pings development sandbox
#

DIRS = "."
DIRPATH="~/projects/p/pinger"

GIT_VERSION := $(shell git describe --abbrev=4 --dirty --always --tags)

HOSTS = waffle pancake
PUSH_FILES = $(HOSTS:%=.%_push)

help: ${FORCE}
	cat Makefile

SOURCE = \
	analyze_pings.py \
	LineQueue.py

FILES = \
	${SOURCE} \
	lqtest.txt \
	Makefile \
	sample.txt

stuff.tar: ${FORCE}
	tar -cvf stuff.tar ${FILES}

DATA = sample.txt

CRUNCHER = analyze_pings.py

test: ${FORCE}
	head -100000 ${DATA} > ${HOME}/tmp/test.txt
	python ${CRUNCHER} -v ${GIT_VERSION} -f ${HOME}/tmp/test.txt

run: ${FORCE}
	python ${CRUNCHER} -v ${GIT_VERSION} -f ${DATA}

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

log: .gitattributes
	git log --pretty=oneline

# Distribution to other hosts

push: ${PUSH_FILES}
	rm ${PUSH_FILES}

.%_push:
	rsync -az --exclude=".git*" --exclude=".*_push" -e ssh ${DIRS} $*:${DIRPATH}
	touch $@

FORCE: 
