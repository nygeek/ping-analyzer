#
# analyze_pings development sandbox
#

DIRS = "."
DIRPATH="~/projects/p/pinger"

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

DATA = sample.txt

CRUNCHER = analyze_pings.py

test: ${FORCE}
	tail -n 500000 ${DATA} | python ${CRUNCHER}

run: ${FORCE}
	cat ${DATA} | python ${CRUNCHER}

lqtest: ${FORCE}
	python LineQueue.py

pylint: ${SOURCE}

commit: ${FILES}
	git commit ${FILES}

log: ${FORCE}
	git log --pretty=oneline

.%_push:
	rsync -az --exclude="RCS" --exclude=".*_push" -e ssh ${DIRS} $*:${DIRPATH}
	touch $@

FORCE: 
