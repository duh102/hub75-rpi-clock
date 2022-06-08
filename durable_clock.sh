#!/bin/bash
set -eu
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games
loc="$(dirname "$(readlink -f "$0")")"
cd "${loc}"
sleep 120
su juggernaut -c 'pushover --title "RPi Clock INFO" "Starting durable script" --priority -1'

for i in 1 2 3 4 5; do
  ./clock.py > "output${i}.txt" 2>"err${i}.txt" && true # using the fakeout to prevent set -e from interfering in restarting the script
  if [ "$i" -lt 5 ]; then
    su juggernaut -c 'pushover --title "RPi Clock ERROR" "Clock exited, restarting in 30 seconds" --priority 1'
    sleep 30
  fi
done

su juggernaut -c 'pushover --title "RPi Clock ERROR" "Clock exited, reached end of retries" --priority 1'
