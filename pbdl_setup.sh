#!/bin/bash

setup() {
	if [ "$(test_setup)" -eq 1 ]; then
		sudo apt-get install -y transmission-daemon transmission-cli transmission-remote-gtk
	fi
}

test_setup() {
	hastrans=$(which transmission-daemon)
	if [ -z "$hastrans" ]; then
		echo 1
	else
		echo 0
	fi

}

start() {
	sudo transmission-daemon -f --log-level=debug >> "$HOME/.transmission-daemon.log"&
	echo "Daemon running!"
}

stop() {
	sudo kill $(getpid)
	echo "Daemon stopped!"
}

getpid() {
	data=($(pgrep -af transmission-daemon | cut -d ' ' -f 1))
	echo "${data[1]}"
}

test_running() {
	pid=$(getpid)
	if [ -n "$pid" ]; then
		echo "1"
	else
		echo "0"
	fi
}

if [ "$(test_setup)" == "1" ]; then
	setup
fi
if [ -n "$1" ]; then
	if [ "$1" == "-s" ] || [ "$1" == "--start" ]; then
		start
	elif [ "$1" == "-k" ] || [ "$1" == "--stop" ] || [ "$1" == "--kill" ]; then
		stop
	fi
else
	if [ "$(test_running)" ]; then
		stop;
	else
		start;
	fi
fi
