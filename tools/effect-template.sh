#!/bin/sh
# Template for a bounded effect that runs on the doorbell. Copy it, rename it, then fill in effect() and restore().
# Run it as: sh /tmp/<name>.sh start | stop      (a reboot clears /tmp; /etc/persistent keeps the file but nothing starts it)
# With an SSH key limited by command="sh /etc/persistent/<name>.sh", the word typed after the host arrives in $SSH_ORIGINAL_COMMAND.
# The pattern: one effect at a time; a detached watchdog restores the device if nothing else does;
# a PID is killed only after checking it still belongs to this script.
SELF=$(basename "$0")                 # keep the file name unique: killold matches on it
STATE=/tmp/$SELF
DURATION=${DURATION:-30}              # watchdog length in seconds

killold() { # kill the PID stored in file $1 only if that process is still one of these scripts; PIDs get reused
  p=$(cat "$1" 2>/dev/null)
  [ -n "$p" ] && grep -q "$SELF" "/proc/$p/cmdline" 2>/dev/null && kill "$p" 2>/dev/null
  return 0
}
restore() { echo "restore $(date +%T)" >> "$STATE.log"; }                      # put everything back to normal
effect()  { echo "effect  $(date +%T)" >> "$STATE.log"; sleep 2; }             # what you want to show
watchdog() { killold "$STATE.wd"; ( sleep "$DURATION"; restore; rm -f "$STATE.wd" ) >/dev/null 2>&1 & echo $! > "$STATE.wd"; }
one_at_a_time() { killold "$STATE.fx"; echo $$ > "$STATE.fx"; }

case "${1:-$SSH_ORIGINAL_COMMAND}" in
  start) one_at_a_time; watchdog; effect ;;
  stop)  killold "$STATE.fx"; killold "$STATE.wd"; rm -f "$STATE.wd"; restore ;;
  *) echo "usage: $0 start|stop" >&2; exit 2 ;;
esac
