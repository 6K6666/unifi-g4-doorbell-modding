# Instructions for AI coding assistants

This repository documents how to explore and modify a UniFi G4 Doorbell Pro. A person is probably running you against their own doorbell, on a home network, behind a video recorder they rely on. Read this file before you run any command on the device.

## What the repository is

Research notes, tested recipes and small tools for a G4 Doorbell Pro (system ID `0xa574`, firmware 5.5.45): how to get a shell, what runs inside, and how to drive the button ring, spotlight, screen and ring tone. `examples/halloween-2026/` is one finished project built from them. Start with [docs/README.md](docs/README.md). Plain-language terms are in [docs/glossary.md](docs/glossary.md).

## Before you touch the device

Ask the user, and do not guess:

1. Is SSH working? Have them run `ssh ubnt@DOORBELL_IP`. If it is refused, follow [docs/getting-started/getting-ssh-access.md](docs/getting-started/getting-ssh-access.md) with them. Do not look for credentials on their machine.
2. Which model and firmware? `grep -E 'sysid|name' /etc/board.info` and the firmware version in Protect. This repository's findings are for `0xa574`, 5.5.45. If it differs, treat every recipe as unverified and say so.
3. What do they want: read-only exploration, a reversible change, or something lasting? Do the smallest thing that meets it.
4. Can someone watch the doorbell? Lights, screen and sound cannot be verified from a log alone. Ask them what they saw.

## Rules

- Read-only first. List files, read logs and sysfs values before you change anything.
- Ask before every command that changes state, and say what it changes and how to undo it. Reversible changes are in [docs/how-to/quick-start.md](docs/how-to/quick-start.md) and [docs/how-to/undo-and-recovery.md](docs/how-to/undo-and-recovery.md).
- Never run, without an explicit yes from the user for that exact command: `Reboot`, `ResetToDefaults`, `UpdateFirmwareRequest`, anything in `mcu_upgrade.sh` or `urc_upgrade.sh`, anything that writes to `/dev/spidev*`, `/dev/mtd*` or `/dev/fb*`, `i2c_access*` or `amba_debug` writes, remounting `/` writable, or changes to accounts, passwords or Wi-Fi. They can brick the device or drop it from the NVR.
- Do not restart `ubnt_avclient` or Protect. Restarting Protect paused recording on every camera; restarting the doorbell's own link to the NVR was not tested and is not worth the risk.
- Do not search the doorbell's filesystem recursively. It runs near 100% CPU; a recursive `grep` slowed the whole device. Copy files off with [tools/copy-files.sh](tools/copy-files.sh) and search the copy.
- `statusCode 0` from `ubnt_ipc_cli` means delivered, not applied. Read `logread | tail` and the saved config under `/etc/persistent`, and ask the user what they saw.
- Never send a whole saved config file to `ChangeSoundLedSettings`. Send the one key you want to change, one family of settings per message.
- The NVR overwrites screen, sound and LED settings at times of its own choosing. If a change disappears, check that before debugging your script.
- Leave the device as you found it. End every test by running the undo, and confirm with the user.
- Keep scripts bounded: a watchdog that restores state, one effect at a time, checked PID kills. Use [tools/effect-template.sh](tools/effect-template.sh).

## Secrets and privacy

- Never write the recovery code, SSH private keys, certificates, password hashes, Wi-Fi settings or MAC addresses into a file, a commit, a pull request or chat. Do not ask the user to paste them.
- Use the placeholders `DOORBELL_IP`, `HOME_ASSISTANT_HOST` and `UDM_IP` in anything you write to the repository.
- Do not copy `/etc/persistent` wholesale off the device. It holds the SSH host key and controller certificates.
- Do not commit Ubiquiti's binaries, sounds or images, or the user's backups. `.gitignore` already excludes the usual paths; do not work around it.
- If you generate an SSH key for another machine to use, restrict it with a forced command and remove it afterward. See [docs/how-to/running-custom-scripts.md](docs/how-to/running-custom-scripts.md).

## Writing documentation here

- Label every claim with how it was checked: run, seen, logged, strings or stock script. A name found with `strings` is a lead, not a result. See [docs/README.md](docs/README.md).
- Say what you did not test. A finding without its caveat is a bug in the docs.
- Write for hobbyists: short sentences, plain words, no jargon without a gloss, commands that can be pasted. Use specific numbers and names. Skip hype, filler, em dashes and bold label lists.
- Headings name what a section holds. Do not tease.
- Test a recipe on the device before you add it. If you cannot, mark it untested and put it under "Not working yet" in [docs/how-to/recipes.md](docs/how-to/recipes.md).

## Quick facts

| Thing | Value |
|---|---|
| Login | `ssh ubnt@DOORBELL_IP`, password is the recovery code until a key is installed |
| Keys go in | `/etc/dropbear/authorized_keys` (not `~/.ssh`); newer OpenSSH needs `-o HostKeyAlgorithms=ecdsa-sha2-nistp256` |
| Copy files to the device | `scp -O` (no SFTP server) |
| Writable and persistent | `/etc/persistent` only (7.6 MB, scripts run from it, nothing starts them at boot) |
| In memory, cleared on reboot | `/tmp`, `/var`, `/etc` |
| Ring | `ubnt_ipc_cli -T=ubnt_mcu_agent` with `SetLEDStatus`; stock look is `fgColor` 4, `bright` -1 |
| Orange, yellow | ring red plus `/sys/class/leds/G/brightness` 25, 60 |
| Spotlight | read `i2cget -f -y 2 0x63 0x0a` and `0x0b`, then `/sys/class/leds/torch1/brightness` (10 of 127 is visible) |
| Screen | `ubnt_ipc_cli -T=ubnt_lcm_gui`, `ShowGui` and `ChangeLcmGuiSettings` with `customAnimations` (merged by `guiId`; disable with `"enable":false`) |
| Ring tone | `ChangeSoundLedSettings` with only `customSounds`; file and `.md5` in `/etc/persistent/sounds/` |
| Log | `logread \| tail` |
| Message names | [docs/reference/data/ipc-names.txt](docs/reference/data/ipc-names.txt) |

## Tools

- [tools/copy-files.sh](tools/copy-files.sh): copy the doorbell's scripts and stock configs to your machine at low priority
- [tools/extract-ipc-names.py](tools/extract-ipc-names.py): list message names in copies of the service programs
- [tools/install-ssh-key.sh](tools/install-ssh-key.sh): put your key where Dropbear reads it
- [tools/effect-template.sh](tools/effect-template.sh): the bounded-effect pattern as a starting point

## If the firmware differs

Run `tools/copy-files.sh`, copy the service programs from `/bin`, run `tools/extract-ipc-names.py`, and diff the output against `docs/reference/data/ipc-names.txt`. Report differences to the user before you trust any recipe.
