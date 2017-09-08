#
# analyze_pings development sandbox
#

DIRS = "."
DIRPATH="~/projects/p/pinger"

HOSTS = waffle pancake
PUSH_FILES = $(HOSTS:%=.%_push)

help: ${FORCE}
	cat Makefile

FILES = \
	Makefile \
	sample.txt \
	analyze_pings.py

DATA = sample.txt

CRUNCHER = analyze_pings.py

test: ${FORCE}
	tail -n 100000 ${DATA} | python ${CRUNCHER}

run: ${FORCE}
	cat ${DATA} | python ${CRUNCHER}

.%_push:
	rsync -az --exclude="RCS" --exclude=".*_push" -e ssh ${DIRS} $*:${DIRPATH}
	touch $@

FORCE: 
