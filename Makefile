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
	insert_timestamps.py \
	LICENSE.md \
	LineQueue.py \
	Makefile \
	pinger.py \
	README.md \
	TimeStamp.py

DATA = \
	data/sample.txt \
	data/2017-11-26-15.38.txt

FILES = \
	${SOURCE} \
	.gitignore \
	pinger.cfg \
	lqtest.txt \
	weird.cfg

stuff.tar: ${FORCE}
	tar -cvf stuff.tar ${FILES}

DATA = data/sample.txt

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

status: ${FORCE}
	git status

commit: .gitattributes
	git commit ${FILES}
	git push -u origin master
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
