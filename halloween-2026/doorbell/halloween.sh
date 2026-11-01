#!/bin/sh
# Haunted Witch Cat: doorbell-side effects. Run as: sh /tmp/halloween.sh <command>
# Also used as the forced command for the temporary Home Assistant SSH key (command is read from SSH_ORIGINAL_COMMAND).
# Every effect is bounded; a detached watchdog restores stock state if nothing else does.
L=/sys/class/leds
I2C="i2cget -f -y 2 0x63"
PIDF=/tmp/halloween.wd
ANIM=/etc/persistent/lcm/animation

killold() { # kill the PID stored in file $1 only if that process is still one of these scripts; PIDs get reused
  p=$(cat "$1" 2>/dev/null)
  [ -n "$p" ] && grep -q halloween "/proc/$p/cmdline" 2>/dev/null && kill "$p" 2>/dev/null
  return 0
}

ring() { # fg bright [green]
  ubnt_ipc_cli -T=ubnt_mcu_agent -r=0 -t=1500 -m="{\"functionName\":\"SetLEDStatus\",\"mode\":1,\"fgColor\":$1,\"bgColor\":0,\"bright\":$2}" >/dev/null 2>&1
  echo "${3:-0}" > $L/G/brightness
}
spot() { # level 0-127; clearing the LM3644 fault flags first is what makes torch mode stick
  if [ "$1" -gt 0 ]; then $I2C 0x0a >/dev/null; $I2C 0x0b >/dev/null; fi
  echo "$1" > $L/torch1/brightness
}
wake() { ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m='{"functionName":"ShowGui","guiId":"WELCOME","welcomeType":"image","brightness":60}' >/dev/null 2>&1; }
screenwatch() { # keep the cat on screen: wake the display right after each stock auto-off. Ends when stock() removes the idle marker, a newer watcher starts, or at expiry.
  tok="$$-$(date +%s)"; echo "$tok" > /tmp/halloween.scrwd; wake
  ( while [ -f /tmp/halloween.idle ] && [ "$(cat /tmp/halloween.scrwd 2>/dev/null)" = "$tok" ] && [ "$(date +%s)" -lt 1793512800 ]; do
      logread | grep "LCM brightness" | tail -1 | grep -q "Auto-off active" && wake
      sleep 4
    done ) >/dev/null 2>&1 &
}
pulse() { # armed idle ring: hardware breathing red (mode 4) over a steady little green, chosen by eye
  echo 12 > $L/G/brightness
  ubnt_ipc_cli -T=ubnt_mcu_agent -r=0 -t=1500 -m='{"functionName":"SetLEDStatus","mode":4,"fgColor":1,"bgColor":0,"bright":60,"breathingPeriodMs":3000,"breathingEndsMs":0}' >/dev/null 2>&1
}
restore() { # end of a show: back to the armed idle ring if armed, else stock
  spot 0
  if [ -f /tmp/halloween.idle ]; then pulse; else ring 4 -1; fi
}
stock() {
  rm -f /tmp/halloween.idle
  killold /tmp/halloween.idlewd; rm -f /tmp/halloween.idlewd
  echo 0 > $L/G/brightness
  spot 0
  ring 4 -1
  ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m='{"functionName":"ShowGui","brightness":0}' >/dev/null 2>&1 # screen back to stock: dark until the next visitor wakes it
}
watchdog() { # seconds
  killold $PIDF
  ( sleep "$1"; restore; rm -f $PIDF ) >/dev/null 2>&1 &
  echo $! > $PIDF
}
fx() { # one effect at a time: stop a still-running earlier greet/press before starting another
  killold /tmp/halloween.fx
  echo $$ > /tmp/halloween.fx
}
gui() { ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=4000 -m="{\"functionName\":\"ChangeLcmGuiSettings\",\"customAnimations\":$1}" >/dev/null 2>&1; }

# ponytail: ring colors observed by eye: 1 red, 4 blue, 5 pink; red + G sysfs 25 = orange; mode 4 = breathing.
case "${1:-$SSH_ORIGINAL_COMMAND}" in
  # Armed idle: pulsing green/orange ring. Its own timer returns the ring to stock at midnight even if Home Assistant is gone.
  idle)   : > /tmp/halloween.idle; pulse; screenwatch
          killold /tmp/halloween.idlewd
          n=$((1793512800 - $(date +%s))); [ $n -lt 1 ] && n=1
          ( sleep $n; rm -f /tmp/halloween.idlewd; stock ) >/dev/null 2>&1 &
          echo $! > /tmp/halloween.idlewd ;;
  stock)  stock ;;
  greet)  fx; watchdog 40; ring 5 40; sleep 1; ring 1 50 25
          for l in 4 14 8 16 10 12; do spot $l; sleep 0.25; done; spot 10 ;;
  press)  fx; watchdog 30
          spot 10
          for i in 1 2; do ring 1 20; sleep 0.25; ring 1 70; sleep 0.25; ring 1 20; sleep 0.6; done
          for i in 1 2 3; do ring 1 70 25; sleep 0.4; ring 5 70; sleep 0.4; done
          ring 1 50 25 ;;
  spot_on) watchdog 20; spot 10 ;;
  spot_off) spot 0 ;;
  restore) fx; killold $PIDF; rm -f $PIDF; restore ;;
  display_on)  gui '[{"count":8,"durationMs":1600,"enable":true,"file":"halloween-ringing.png","guiId":"WAITING_FOR_RESPONSE","loop":true},{"count":8,"durationMs":2000,"enable":true,"file":"halloween-welcome.png","guiId":"WELCOME","loop":true}]' ;;
  # The doorbell merges customAnimations by guiId, so the ringing override must be disabled explicitly, not just omitted.
  display_off) gui '[{"count":8,"durationMs":1600,"enable":false,"file":"halloween-ringing.png","guiId":"WAITING_FOR_RESPONSE","loop":true},{"count":1,"durationMs":100,"enable":true,"file":"efe2e540-435d-11b1-29a1-7d5a7391c654.png","guiId":"WELCOME","loop":true}]' ;;
  # Device-local ring sound replaces the stock visitor tone (no doubled playback). Partial payload only: the full-config payload is rejected.
  sound_on)  ubnt_ipc_cli -T=ubnt_sounds_leds -r=0 -t=4000 -m='{"functionName":"ChangeSoundLedSettings","customSounds":[{"enable":true,"file":"halloween-ring.ogg","repeatTimes":1,"soundStateName":"RING_BUTTON_PRESSED","volume":35}]}' >/dev/null 2>&1 ;;
  sound_off) ubnt_ipc_cli -T=ubnt_sounds_leds -r=0 -t=4000 -m='{"functionName":"ChangeSoundLedSettings","customSounds":[{"enable":true,"file":"Default.ogg","repeatTimes":1,"soundStateName":"RING_BUTTON_PRESSED","volume":100}]}' >/dev/null 2>&1 ;;
  sound_check) # reinstall the ring sound if Protect wiped it; master copy lives in /tmp
          if [ ! -f /etc/persistent/sounds/halloween-ring.ogg ] || ! grep -q halloween-ring.ogg /etc/persistent/ubnt_sounds_leds.conf; then
            cp /tmp/halloween-ring.ogg /etc/persistent/sounds/halloween-ring.ogg &&
            md5sum /etc/persistent/sounds/halloween-ring.ogg | cut -d' ' -f1 | tr -d '\n' > /etc/persistent/sounds/halloween-ring.ogg.md5 &&
            sh "$0" sound_on
          fi ;;
  revoke_key) sed -i '/halloween-2026-temp/d' /etc/dropbear/authorized_keys /etc/persistent/.ssh/authorized_keys ;;
  *) echo "denied" >&2; exit 2 ;;
esac
