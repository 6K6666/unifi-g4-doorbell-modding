# Exploring the doorbell safely

The doorbell is a small computer with little spare CPU and memory, and the same machine is recording video and watching the door. These are the habits that worked while surveying it, and the one mistake that did not.

## Copy files off, then search them elsewhere

A recursive `grep` across `/etc`, `/bin` and `/usr` ran for over 90 seconds, outlived the SSH session that started it, and the load average read 8.4 while it ran, against 6.4 a few minutes before. It had to be found with `ps` and killed. Use targeted reads on the doorbell and do the searching on another machine:

```sh
ssh ubnt@DOORBELL_IP 'cd / && nice -n 19 tar cf - usr/etc/conf bin/*.sh usr/local/bin/*.sh' | tar xf - -C ./doorbell-files
```

`nice` and an uncompressed tar kept the copy from competing with the video pipeline. About 880 KB of text files and 7 MB of service binaries were copied this way.

## What to copy, and what to leave

Worth copying:

- every shell script in `/bin`, `/usr/bin`, `/usr/lib` and `/usr/local/bin`; they are the firmware's own documentation
- `/usr/etc` configs: `conf/`, `gui/*.json`, `features*.json`, `rc.d/`, `lighttpd/`
- the service binaries, for `strings`; leave out the 17 MB `ubnt_smart_detect` unless you need it

Leave on the doorbell:

- `/etc/persistent` as a whole: it holds the SSH host key, certificates and account data
- `/etc/passwd`, `/etc/wlan0.conf`, and in `/usr/etc` the files `sysclean.cfg` and `system-a574.cfg`, which carry the firmware's default account hashes

Nothing copied for this repository includes those. A keyword search for `psk` and `passphrase` over the copied scripts matched shell variables and the support-bundle sanitizer's patterns; the Wi-Fi setup script takes the password as an argument. Read the matches before you share any copy.

## Read before you write

- `strings` on a service binary lists its message names, config keys and log messages. The log messages are often the best hint about why something failed.
- The stock factory scripts in `/usr/local/bin` show the exact arguments Ubiquiti's own tests use. They pointed to settings the earlier attempts had not used.
- `logread` shows each service's reaction to a message. Check it after every call, because `statusCode 0` only means the message was delivered.

## Reversible tests

- Prefer a test with a built-in undo: set a value, read it back, put the old value back in the same command with `trap`.
- Check the saved config after a change. `/etc/persistent/*.conf` shows what the service kept.
- Keep a copy of the stock files before any change (see the backups README in the season folder).

## What not to touch without a plan

- `/dev/spidev1.1`, the MTD devices and the I2C tools: they bypass the drivers and have no confirmation.
- Messages that reset, reboot, update or re-flash (listed in the [IPC reference](ipc-and-services.md)).
- Anything that restarts `ubnt_avclient`: the doorbell drops its link to the NVR and recording pauses.
