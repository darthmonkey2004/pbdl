#!/bin/bash

go=1
pos=0
while [ "$go" -eq 1 ]; do
	pos=$(( pos+1 ))
	echo "$pos" >> '/home/monkey/test.txt'
	sleep 5
done
