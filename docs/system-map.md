# System map: processes, boot, network

What runs on a UniFi G4 Doorbell Pro (board G4R, system ID 0xa574, firmware 5.5.45) and how it starts. Surveyed on 2026-10-31 with read-only commands over SSH. Evidence labels used across these docs:

- run: executed during this project and the result observed
- seen: a person watched or listened and reported
- logged: shown by the doorbell's log or a readback
- strings: read from the stock binaries with `strings`, not tried
- stock script: read in the firmware's own shell scripts, not run here

## Platform

| Item | Value | Label |
|---|---|---|
| SoC | Ambarella, kernel hardware string "Ambarella UVCDOORBELL Board - Pro", four ARMv8 cores (CPU part 0xd03) | run |
| Memory | 246 MB total, about 22 MB free at the survey | run |
| Kernel | Linux 4.9.184, aarch64, PREEMPT | run |
| Userland | BusyBox 1.37.0, glibc 2.23, Dropbear 2020.81, lighttpd | run |
| Network | `wlan0` only (Broadcom `bcmdhd` driver); no wired interface on this model | run |
| Variants | The PoE doorbell is a separate system ID, 0xa575, with its own feature file and a KTD2061 LED driver this unit lacks | stock script |

The board's feature flags (`/etc/board.info`) include LCD screen, NFC, fingerprint, smart detect, AEC audio, chime control, IR LED and status LED. They list no battery, RTC, accelerometer or PIR.

## Load

The CPU is close to saturated during normal operation. One `top` snapshot: 48% user, 43% system, 6.5% idle, load average 6.4, with `ubnt_smart_detect` using about a third of the CPU, a Wi-Fi `wl noise` survey 17%, `ubnt_streamer` 11% and `ubnt_ispserver` 6.5%. Free memory sat around 22 MB.

Two consequences for anyone modifying the doorbell:

- A recursive `grep` over the filesystem ran past 90 seconds, and the load average read 8.4 while it ran, against 6.4 a few minutes before. Search copies of the files on another machine instead (see [exploring the doorbell safely](exploring-the-doorbell-safely.md)).
- A shell loop that reads the whole log every few seconds is not free. `logread` held about 1.1 MB, and ten reads with `grep` took 4 seconds of wall time on the saturated CPU. A `logread -f` stream avoids rereading the buffer.

## Flash layout

`/proc/mtd` lists nine partitions:

| Partition | Size | Notes |
|---|---|---|
| bst | 128 KB | boot stage |
| bld | 1 MB | bootloader |
| ptb | 896 KB | partition table |
| spl | 1 MB | |
| pri | 8 MB | |
| urc | 48 MB | recovery image (a script reads its first 128 bytes for a version string) |
| lnx | 144 MB | holds the UBI volume `rootfs` |
| log | 16 MB | UBI volume `persistent-log`, mounted at `/mnt/log` |
| cfg | 16 MB | UBI volume `cfg`, mounted at `/var/etc/persistent` |

The mounts that matter, from `mount` and `df`:

| Mount | Type | Writable | Size |
|---|---|---|---|
| `/` | UBIFS `rootfs` | no (`ro`) | 90.6 MB, 78% used |
| `/var` | tmpfs | yes | 120 MB |
| `/var/etc/persistent` (also `/etc/persistent`) | UBIFS `cfg`, `sync`, zlib | yes | 7.6 MB, 652 KB used |
| `/mnt/log` | UBIFS `persistent-log`, `noexec` | yes | 7.6 MB, 61% used |
| `/run`, `/mnt` | tmpfs | yes | |

The kernel command line is `console=ttyS0 ubi.mtd=lnx root=ubi0:rootfs ro rootfstype=ubifs init=/linuxrc`. [Filesystem and persistence](filesystem-and-persistence.md) covers what each of these means for modifications.

## Boot sequence

1. The kernel mounts the UBIFS root read-only and runs `/linuxrc`.
2. `/linuxrc` mounts `/proc`, `/sys`, a tmpfs `/var`, devtmpfs `/dev` and `/run`, starts `syslogd` (1 MB ring), and sets the clock to 2000-01-01 until the network corrects it.
3. It rebuilds `/etc`, which is a symlink to `/var/etc` on tmpfs: some files are always copied from `/usr/etc` (`inittab`, `rc.d`, `modules.d`, `udev` and others), some only if missing (`passwd`, `group`, `hosts`, `startup.list`), and the rest become symlinks into `/usr/etc`.
4. It runs `boarddetect` to write `/etc/board.info`, then init reads `/etc/inittab`.
5. `rc.sysinit` loads kernel modules and applies board settings; `ubnt_migrate` upgrades old config versions; init starts the services below.

The stock `/usr/etc/inittab` in the image has 19 lines and no services. The running `/etc/inittab` has 53, including every service listed next. Its modification time, 17:33, is within seconds of Dropbear's first start in the log (17:33:37), after SSH was enabled through Protect. So the running file is not a plain copy of the image's file. Where the service lines come from is an open question: no copied script or binary mentions them.

Helper functions in `/usr/lib/ubnt_utils.sh` (`enabling_service`, `disabling_service`, `enable_services`) switch a service by commenting or uncommenting its `inittab` line and running `init -q`. They are the likely mechanism behind the controller's `StartService` and `StopService` commands (stock script; not confirmed).

## Services

Every service is respawned by init. Memory is resident size at the survey.

| Process | Role | Notes |
|---|---|---|
| `ubnt_avclient` | link to the Protect NVR; receives settings and forwards them | 88 MB; 127 command names (strings) |
| `ubnt_ctlserver` | device control: thermal, time zone, reboot, save to flash | 27 MB |
| `ubnt_sounds_leds` | sounds, ring LED, spotlight, scene logic | 147 MB virtual |
| `ubnt_lcm_gui` | the 240 by 240 screen | 35 MB |
| `ubnt_mcu` (via `mcu_launcher.sh`) | talks to the microcontroller that owns the button ring | Go binary, 110 MB virtual |
| `ubnt_streamer`, `ubnt_ispserver`, `ubnt_osd` | video encoding, image pipeline, overlays | |
| `ubnt_smart_detect` | person, vehicle, animal and package detection | 17 MB binary, heaviest process |
| `ubnt_talkback`, `ubnt_audio_events` | two-way audio, sound event detection | UDP 7004 for talkback |
| `ubnt_nfc`, `ubnt_fingerprint`, `ubnt_access`, `ubnt_uahubl2` | NFC reader, fingerprint sensor, access control, door hub link | |
| `ubnt_networkd`, `wpa_supplicant`, `udhcpc` | Wi-Fi and addressing | |
| `ubnt_watchdog`, `ubnt_reportd`, `infctld` | watchdog, reporting, UBNT discovery | UDP 10001 for discovery |
| `lighttpd`, `dropbear` | web server and SSH | |
| `crond` | hourly log rotation and crash cleanup only | |

The binaries live in `/bin` (also reachable as `/usr/bin`). Several `ubnt_*` names are tiny symlinks to a larger program; `uvcbox` is a 9.8 MB multi-call binary.

## Network exposure

| Port | Service | Notes |
|---|---|---|
| TCP 22 | Dropbear | closed until Protect's SSH setting is on; see [getting SSH access](getting-ssh-access-to-the-doorbell.md) |
| TCP 80, 443 | lighttpd | `/api/*` is rewritten to `rest.cgi` (`ubnt_cgi`); snapshots at `/snap.jpeg` and numbered variants go through an auth module; `/teleport/ws` proxies to a local service on 7447 |
| UDP 7004 | `ubnt_talkback` | two-way audio |
| UDP 10001 | `infctld` | device discovery |

The web server's auth module leaves five services open before login (`login`, `version`, `connect`, `manage`, `snapshot`); the web interface itself was not exercised.

## Hourly jobs

`crond` runs three jobs: `logrotate`, `cleanup-stackdump` and `crash-report`. Core dumps are piped through `/bin/coredump_light.sh`.
