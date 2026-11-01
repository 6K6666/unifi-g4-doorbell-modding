# Halloween 2026: build log and review

The goal was a one-night show on the front-door G4 Doorbell Pro and four LIFX bulbs: a purple and orange idle, an orange wave when the driveway camera sees a person, a greeting when the doorbell does, and a cat, a sound and a light routine when someone presses the button. The original request is in [SPEC.md](../SPEC.md). Mode was armed at 6:53:47 PM MDT on October 31 and expires at midnight.

This page records the order things happened in, what broke, what was still unproven when the show went live, and what to do differently next time.

## Timeline

All times are MDT, October 31, from the doorbell log and Home Assistant history.

| Time | Event |
|---|---|
| before 5:52 PM | An earlier session backed up the doorbell config, built the two cat animations, and tried two ways to light the ring (the `R` channel and `ChangeSoundLedSettings`). Neither changed the ring. |
| 5:54 PM | Read-only survey of the doorbell: LED drivers, services, IPC functions. |
| 5:57 PM | First ring response, through the microcontroller agent's `SetLEDStatus`. |
| 6:02 to 6:10 PM | Ring colors mapped by eye; green from the `G` channel found; the spotlight lit on some commands and not others, and clearing a latched flag register first made it light on three of three. |
| 6:10 PM | Both cat animations installed on the doorbell. |
| 6:21 to 6:30 PM | Home Assistant package installed. The doorbell rejected the temporary SSH key twice; fixed by using Dropbear's own key file and forcing the ECDSA host key. |
| 6:33 PM | Preview buttons pressed; nothing happened. Cause: a trigger condition that rejected the first press. |
| 6:34 to 6:38 PM | Previews ran but the bulbs ignored them. A LIFX app effect was overwriting every command. Stopped in the app at about 6:37. |
| 6:38 PM | First preview that worked end to end, watched through the doorbell camera tile in Chrome. |
| 6:40 to 6:50 PM | Independent review, fixes, and the sounds. At 6:46:57 PM a Home Assistant volume change made Protect wipe the custom ring sound. |
| 6:51:17 PM | First real button press with the custom sound. It played; the viewer reported a delay. |
| 6:53:47 PM | Halloween Mode turned on. |
| 7:02:49 PM | Screen watcher started; the cat stayed on screen afterward. |

## What was built

A Home Assistant package ([halloween_2026.yaml](../homeassistant/halloween_2026.yaml), 488 lines) that defines seven scripts, eleven automations and 32 entities in all, counting the helpers, scripts and automations. A shell script ([halloween.sh](../doorbell/halloween.sh), 86 lines) that runs on the doorbell and is the only thing the temporary SSH key can run. A Python script ([make_sounds.py](../doorbell/make_sounds.py)) that synthesizes the two cat sounds with additive vocal synthesis, so no recordings or audio libraries are needed.

Home Assistant never animates the doorbell frame by frame. It sends one word (`greet`, `press`, `idle`, `stock`, `restore`, `display_on`, `display_off`, `sound_on`, `sound_off`, `sound_check`, `revoke_key`) and the script on the doorbell runs the effect locally. Each effect ends in a detached timer that returns the ring and spotlight to a known state if no later command arrives.

## Problems found, in chronological order

### The ring is not on the LED channels that look like a ring

`/sys/class/leds` lists `R`, `G`, `B` and `W`, which looks like a ring. Only `G` changes anything the viewer could see, and it adds green to a ring that red comes from elsewhere. The first dead-end tests ran at 5:47 PM in the earlier session, and the first ring response came at 5:57 PM. The step that worked was searching the stock binaries for the names of the services that handle LED messages, which led to `ubnt_mcu_agent` and its `SetLEDStatus`. Next time, find the process that owns the hardware before probing the hardware.

### A trigger condition dropped the first event

The spec says to ignore unavailable and unknown transitions. The first version rejected any state change coming from `unknown`. An `input_button` that has never been pressed is `unknown`, and so is the doorbell event entity after a restart. Both previews did nothing, and a real first ring after a restart would have been dropped the same way. The condition now rejects only `unavailable`, and a 15-second age check on the event timestamp handles stale events at startup. Nineteen template tests (expiry boundary, stale and fresh events, each cooldown, vehicle events) pass on the live Home Assistant.

### The idle loop would have overwritten the wave and the greeting

Only the ring show stopped the idle loop. With the mode on, the loop would have repainted the driveway lights every seven seconds over the orange wave and over the greeting's front-door brightness. Every preview before arming ran with the mode off, which hid it. An independent review caught it and both scripts now stop the loop first. A fast walker could also have lost the greeting, because it required the approach script to be finished; the greeting now cancels the approach script instead.

### Restoring the screen left the ringing cat in place

`display_off` sent the original welcome entry and omitted the ringing entry. The doorbell merges by screen name, so the ringing cat survived. This was found by running the restore commands before arming and reading the saved config. The restore now sends the ringing entry with `enable:false`. That the stock "Ringing" screen comes back was confirmed in the saved config only, not on the screen.

### Protect erased the ring sound

Setting the speaker volume through Home Assistant, to play a quiet meow, appears to have made Protect push its settings; the evidence is timing, one second apart. The custom ring sound reverted to the stock file and the new file was deleted. The approach meow and the volume change were removed, and a check every two minutes reinstalls the ring sound if it is missing. The approach meow also switches the screen to the stock talking image while it plays, so it is off by default.

### A bulb effect from the LIFX app overrode Home Assistant

The four bulbs showed a red-to-orange effect started in the LIFX app. Home Assistant accepted every command and read the new color for about three seconds before the bulbs went back. Neither `light.turn_on` with `effect_stop` nor `lifx.effect_stop` stopped it. Stopping it in the app fixed it. Reading the history for the four lights showed no state changes during the previews, which is how the problem was separated from the earlier trigger bug.

### The doorbell's own midnight timer would have killed itself

The idle command starts a background timer that runs `stock` at the expiry time and records the timer's PID in a file. `stock` begins by killing the PID in that file, which inside the timer is the timer itself, so the ring and screen restore would never have run. It was found while replacing the blind kills with checked ones. The timer now deletes its PID file before calling `stock`. A run with a seven-second expiry removed the idle marker, read back 0 on the green channel and spotlight, and sent the ring reset; nobody watched the ring.

### The midnight automation would have fired every night

The date check was on or after November 1, so the automation would have run again on November 2 and later. Combined with the retry triggers at 12:10 AM and 1:00 AM, the second run after a clean shutdown would have raised the "Halloween restore incomplete" and "Halloween key not revoked" notifications because the private key was already deleted. The check is now equality with November 1, and after a confirmed revocation the automation turns itself off.

## What was verified before arming, and what was not

Verified by eye or by readback:

- The ring colors, the breathing mode and orange and green mixing.
- The spotlight lighting three times out of three.
- The orange wave stepping through lights 1, 2, 3 and the front door (history only; which bulb sits nearest the street is unconfirmed).
- The ring show on the doorbell camera tile: red pulses, then orange and purple on the driveway lights, with the front door steady at 180 of 255.
- The ring sound installed, playing and being repaired after its file was deleted on purpose.
- The restore commands for screen, sound and ring, each returning 0 and leaving the expected saved config.
- The screen staying lit with the watcher running.

Not verified when the mode was turned on:

- A real driveway detection starting the wave, and a real doorbell person event starting the greeting.
- A press with the mode on: the cat's ringing screen on the doorbell, and the ring pulse coming back afterward.
- The Stop & Restore button end to end (each doorbell command and the light restore were tested alone).
- Whether `ShowGui` with brightness 0 darkens the screen. The `stock` command ran once end to end in a timer test and sent the call, but nobody watched the screen or the ring.
- The doorbell's 30 to 40 second timers firing after the SSH session ends. The longer midnight timer was confirmed alive; the show timers were not watched expiring.
- Whether the stock night glow and the spotlight script fight when a real person walks up.
- The second press of the ring sound, which should skip the one-second conversion.
- A doorbell reboot while armed: `/tmp` would lose the script, the master copy of the sound, the SSH key line and every timer. The show would stop working without raising an alert.

The spec asked for the idle lighting to return eight seconds after the press. The ring show runs for about seven seconds and then waits eight more, so lighting returns at about fifteen seconds. This is reported and not yet changed.

## Security notes

The temporary key was generated on Home Assistant with no passphrase and authorized on the doorbell with a forced command. A stolen copy of the private key could run only the named `halloween.sh` words. Home Assistant's SSH add-on runs as root and holds that key at `/config/.ssh/halloween_ed25519`, which the midnight automation deletes after the doorbell confirms the key line was removed. If the doorbell is unreachable at midnight the key and a notification both remain, and the automation retries at 12:10 AM and 1:00 AM.

The persistent authorized_keys file on the doorbell was restored to its original two lines after the failed attempt. The line for the temporary key lives in `/etc/dropbear/authorized_keys`, which probably does not survive a doorbell reboot. That was not tested.

## Changes made to each system

| System | Change |
|---|---|
| Doorbell, flash | `/etc/persistent/ubnt_lcm_gui.conf` (two `customAnimations`), `ubnt_sounds_leds.conf` (one `customSounds`), four files in `lcm/animation/`, two in `sounds/` |
| Doorbell, runtime | one line in `/etc/dropbear/authorized_keys`; files and timers under `/tmp` |
| Home Assistant | `/config/packages/halloween_2026.yaml`, `/config/www/halloween/meow-curious.mp3`, `/config/.ssh/` (key pair and known hosts), one core restart |
| LIFX bulbs | state only; the app effect that was running is gone |

Originals were saved to a local `backups/` folder that is not in the repository; its README lists what to save. The two Ubiquiti binaries used for reading strings are not in the repository either; pull them from `/bin` on the doorbell if needed.

## For the next season

- Put the expiry in one place. The package repeats the 1793512800 epoch seven times and the doorbell script twice. A single `input_datetime` plus a template would avoid a missed edit.
- Run the restore path before arming, and run one full cycle with the mode on and nobody around: on, idle for a minute, simulated approach, simulated press, off.
- Treat any setting kept in `ubnt_sounds_leds.conf` as temporary and add the repair check on day one. The binary reports `supportCustomRingtone`, so uploading the sound through Protect, which owns the setting, is worth trying. It was not tried.
- Keep Chrome open on the Home Assistant dashboard with the doorbell camera tile while testing. It showed the front-door light color and the ring show more reliably than a description from someone standing at the door.
- Check the LIFX app for running effects before testing bulbs.
- Decide before arming what the lights should do at shutdown. Here the snapshot was taken with the bulbs off, so midnight turns them off.
- Check that a stored PID still belongs to the script before killing it (fixed after review). `fx` and the watchdog write PIDs to `/tmp` and kill them on the next run. The doorbell's PID limit is 32768, and its PIDs went from 16819 (the midnight timer, about 6:56 PM) to 20692 (the screen watcher, 7:02 PM), so a stale number can come back as a different process within the hour. The script now reads `/proc/<pid>/cmdline` first and kills the process only if it is one of these scripts; a test with a stale PID and a real script passed.

## Open questions

- Why the ring's green comes from the LP5562 and its red from the microcontroller.
- What modes 0, 2 and 6 of `SetLEDStatus` do. Modes 0 and 2 were dark and mode 6 was not reported.
- What `/dev/spidev1.1` is attached to.
- Whether a person at the door gets the ring show's spotlight and the stock night glow in the same second.
