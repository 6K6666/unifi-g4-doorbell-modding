# Filesystem and persistence

Where files can be changed on the doorbell, what survives a reboot, and what reads them. Labels are explained in the [system map](system-map.md).

## What is writable

| Path | Backing | Survives reboot | Executable |
|---|---|---|---|
| `/` (including `/bin`, `/usr`, `/lib`) | read-only UBIFS image | yes, but cannot be changed while mounted `ro` | yes |
| `/etc` | symlink to `/var/etc`, tmpfs | no, rebuilt by `/linuxrc` | yes |
| `/var`, `/tmp`, `/run`, `/mnt` | tmpfs | no | `/run` is `noexec` |
| `/etc/persistent` | the `cfg` UBIFS volume, mounted `sync` | yes | yes |
| `/mnt/log` | the `persistent-log` UBIFS volume | yes | no (`noexec`) |

`/etc/persistent` is a 7.6 MB volume with about 650 KB used. It is the only place a configuration change can live through a reboot without altering the firmware image.

## What is on the writable volume

File names only; contents include certificates and keys and are not reproduced:

- service configs: `ubnt_lcm_gui.conf`, `ubnt_sounds_leds.conf`, `ubnt_avclient.conf`, `ubnt_encoder.conf`, `ubnt_isp.conf`, `ubnt_access.conf`, `ubnt_audio_events.conf`, `ubnt_fingerprint.conf`, `ubnt_networkd.conf`
- `system.cfg`, the running copy of the board config
- `lcm/animation/` (screen sprites with `.md5` files) and `sounds/` (ring tones with `.md5` files)
- `.ssh/authorized_keys`, `dropbear_ecdsa_host_key`, controller and server certificates
- optional: `https/server.crt` and `https/server.key`, which `/linuxrc` links in place of the stock certificate for the web server if they exist (stock script)

## What reads those files

Each service reads its own config at start and when it receives a settings message. Whether a service notices a hand-edited config file was not tested. The messages that did take effect during this project:

- `ChangeLcmGuiSettings` to `ubnt_lcm_gui` rewrote `ubnt_lcm_gui.conf` and the screen followed (run)
- `ChangeSoundLedSettings` to `ubnt_sounds_leds` rewrote `ubnt_sounds_leds.conf` (run)

Both write the file themselves. The firmware's stock persistence call is `SaveToFlash` on `ubnt_ctlserver`, wrapped by `/bin/ubnt_cmd_persist.sh` (stock script). Writes to `/etc/persistent` land on flash immediately because of the `sync` mount.

## What overwrites your changes

- The Protect controller. It owns the screen, sound and LED settings and re-sends them at times it chooses. One re-send replaced a custom ring sound and deleted its file within a second of a speaker volume change (logged). Anything kept in `ubnt_sounds_leds.conf` needs a repair check. See the [control reference](g4-doorbell-pro-control-reference.md).
- `/linuxrc`, which copies `inittab`, `rc.d`, `modules.d`, `udev` and a few others over `/etc` at every boot, so edits there never survive.
- Firmware updates. A comment in the stock LED script says the updater overwrites the root filesystem in place, and that a shell loop forking `sleep` during the flash crashes because the C library is replaced under it.

## Boot-time execution from persistent storage

Nothing in the copied boot scripts executes a file from `/etc/persistent`. The plugin mechanism (`rc.funcs`, `run_plugin`) sources `/etc/sysinit/<name>.conf` for each name in `/etc/startup.list`, and both locations are on the tmpfs that `/linuxrc` rebuilds: `startup.list` is an empty file copied from the image. No script mentions `rc.local` or a user script directory.

So a reboot clears anything run from `/tmp`: scripts, background timers, temporary SSH keys, converted sounds. A persistent customization has to be reapplied by something outside the doorbell after each boot. This project used Home Assistant for that. This conclusion comes from reading shell scripts only; the compiled services were not checked for their own startup hooks.

## Changing the root filesystem

The root image is mounted read-only and was not remounted during this survey. Remounting it writable (`mount -o remount,rw /`) is the obvious route to persistent changes in `/bin` or `/usr/etc`. It has not been tried. Considerations before anyone does:

- The 90.6 MB volume is 78% full, leaving about 20 MB.
- A firmware update replaces the whole image, so edits last only until the next update, and Protect applies updates on its own schedule.
- The doorbell has no battery. A power cut during a write to flash is possible, and a damaged root image would need the recovery partition (`urc`) or a Ubiquiti recovery procedure.
- Some stock scripts rewrite files in `/etc` and `/etc/passwd` directly (for example `ubnt_cmd_apply_user.sh` writes the login line and signals init), so even the tmpfs side changes underneath you.

## Scripts that change system state

These ship on the doorbell. Read them before running any:

- `mcu_upgrade.sh`, `urc_upgrade.sh`: flash the microcontroller and the recovery image
- `ubnt_cmd_apply_user.sh`: replaces `/etc/passwd` with a single login line, then signals init
- `add_ui_account.sh`, `ubnt_cmd_persist.sh`, `ubnt_cmd_reload_avclient.sh`, `ubnt_cmd_apply_camera_name.sh`: account, persistence and restart helpers
- `Reboot` and `ResetToDefaults` messages to `ubnt_ctlserver`, and `UpdateFirmwareRequest` to `ubnt_avclient`

None of these were run for this survey.
