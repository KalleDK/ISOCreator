#!/usr/bin/env bash

BUILDER="/docker-files/isobuilder.py"
 
if [ -z "$1" ]; then
	echo "Launching ISOBuilder"
	exec "$BUILDER" "rebuild"
	exit $?
fi

if [ "$1" == "build" ]; then
	echo "Launching ISOBuilder"
	exec "$BUILDER" "build"
	exit $?
fi

if [ "$1" == "rebuild" ]; then
	echo "Launching ISOBuilder"
	exec "$BUILDER" "rebuild"
	exit $?
fi

if [ "$1" == "clear" ]; then
	echo "Launching ISOBuilder"
	exec "$BUILDER" "clear"
	exit $?
fi

exec "$@"