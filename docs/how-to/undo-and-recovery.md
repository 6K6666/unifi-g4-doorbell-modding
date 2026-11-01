# Undo and recovery

Risk: none by itself; this page is where you go when something else went wrong.

Everything this repository changes can be put back, and most changes are small. This page lists each change, how to reverse it, and how sure we are that the reversal works. Where a step says "not tested", it was read from the firmware's own scripts or worked out from logs and has not been run.

## Quick reference

| What you changed | How to undo | Tested |
|---|---|---|
| Ring color | `SetLEDStatus` with `fgColor` 4 and `bright` -1, and `echo 0 > /sys/class/leds/G/brightness` | yes |
| Spotlight | `echo 0 > /sys/class/leds/torch1/brightness` | yes |
| Screen shown with `ShowGui` | `ShowGui` with `guiId` `WELCOME`, or wait for the doorbell to dim it | yes |
| Custom screen pictures | send the original `customAnimations` entry again and set any extra entries to `"enable":false` | saved config read back; the screen was not watched |
| Custom ring tone | send `customSounds` pointing at `Default.ogg` with volume 100 | yes |
| Screen kept on by a script | stop the script, then `ShowGui` with `brightness` 0 | the stop ran once; the screen was not watched |
| Script or timer left running in `/tmp` | `ps w`, then `kill` the PID of your script | yes |
| SSH key in `/etc/dropbear/authorized_keys` | delete its line from that file (for example with `sed -i`) | not run |
| Protect's SSH switch (the `enableSsh` override) | delete the override file on the UDM and restart Protect | not tested |

Exact commands for the screen, ring tone and key rows are in the Halloween example's [restore section](../../examples/halloween-2026/README.md#by-hand-if-home-assistant-is-gone).

## Why most changes are low risk

- The root filesystem is read-only, so a typo cannot damage the firmware.
- `/etc`, `/tmp` and `/var` are in memory. Anything left only there disappears when the doorbell restarts.
- The only flash-backed files you touch are small settings and picture and sound files in `/etc/persistent`.

## Things that can still go wrong

- Protect overwrites you. The NVR re-sends its screen and sound settings from time to time. A custom ring tone is the usual casualty; the doorbell falls back to the stock tone, so visitors still hear something. See [filesystem and persistence](../reference/filesystem-and-persistence.md).
- The ring or spotlight stays on. The ring keeps the last color it was sent, and the spotlight stays on until told otherwise. The undo commands above fix both.
- The screen stays blank or stuck. `ShowGui` with `WELCOME` restores it; the next visitor also wakes the stock behavior.
- Recording pauses. Restarting Protect on the NVR interrupted recording on every camera for a few minutes (seen while enabling SSH). Restarting the doorbell's own link to the NVR was not tested; expect the same. Nothing in the quick start does this.
- Locked out of SSH. If the Dropbear key file is cleared (it may be reset when the doorbell restarts; untested), log in with the recovery code as the `ubnt` password and install your key again with `tools/install-ssh-key.sh`.

## When all else fails

Restarting the doorbell clears everything that lives in memory: scripts and timers in `/tmp`, temporary keys, the screen watcher. Settings saved in `/etc/persistent` stay. Restarting from the Protect app or by unplugging the doorbell's power is the usual way; neither was tried on this unit while writing this guide, so expect the NVR to show the doorbell as offline for a minute or two.

Resetting to factory defaults is a last resort and probably removes the doorbell from the NVR. It is outside the scope of this repository.
