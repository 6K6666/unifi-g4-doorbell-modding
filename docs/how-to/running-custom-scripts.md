# Running your own scripts

Risk: medium. Scripts you write can leave the ring, spotlight or screen in a strange state, or load the CPU. Every pattern here is meant to limit that.

The doorbell can run shell scripts, but it has no place to install one so that it starts on its own. This page covers where a script can live, how to start it from outside, and how to write one that cleans up after itself if you walk away. The Halloween show uses every pattern here; see [the example](../../examples/halloween-2026/README.md).

## The short version

- Put the script on the doorbell, in `/tmp` for a one-off or in `/etc/persistent` to keep it through a reboot.
- Something outside the doorbell has to start it: your own computer, Home Assistant, or a scheduled job.
- Give every effect a watchdog that puts things back, so a lost connection never leaves the ring or spotlight stuck.
- Expect the NVR to overwrite some settings, and add a check that puts yours back.

## Where a script can live

| Location | Survives a reboot | Runs |
|---|---|---|
| `/tmp` | no (memory) | yes |
| `/etc/persistent` | yes (flash) | yes; checked by creating a script there and running it with `sh` and directly |
| `/etc`, `/var`, `/run` | no | `/run` is `noexec` |
| `/bin`, `/usr` | yes, but read-only | would need the root remounted writable, which is untried |

`/etc/persistent` is small (7.6 MB) and shared with the doorbell's own settings. Keep scripts short and delete test files. Nothing starts a script from there at boot; the [filesystem notes](../reference/filesystem-and-persistence.md) explain why.

## Starting a script from outside

The simplest start is one SSH command:

```sh
ssh ubnt@DOORBELL_IP 'sh /etc/persistent/myeffect.sh start'
```

To start it from Home Assistant or another machine without handing over a full login, give that machine its own key and limit the key to your script. The doorbell's SSH server supports a forced command in `/etc/dropbear/authorized_keys`:

```
command="sh /etc/persistent/myeffect.sh",no-port-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... my-key-comment
```

With that line, `ssh ubnt@DOORBELL_IP start` always runs `sh /etc/persistent/myeffect.sh` with no arguments, whatever word is typed. The word arrives in the variable `$SSH_ORIGINAL_COMMAND`. So the script must read it when it has no argument and refuse anything it does not know; the key does not filter the words for you. [`tools/effect-template.sh`](../../tools/effect-template.sh) and [`halloween.sh`](../../examples/halloween-2026/doorbell/halloween.sh) both do this.

Two details that cost time:

- Add the key line to `/etc/dropbear/authorized_keys`. The usual `/etc/persistent/.ssh/authorized_keys` is ignored.
- Newer OpenSSH clients, including the one in Home Assistant, need `-o HostKeyAlgorithms=ecdsa-sha2-nistp256`, or the doorbell drops the connection before the key is checked.

In Home Assistant the pattern is a `shell_command` that runs `ssh -i KEYFILE ... ubnt@DOORBELL_IP {{ cmd }}` with one word per action (`greet`, `press`, `restore`). The [Halloween package](../../examples/halloween-2026/homeassistant/halloween_2026.yaml) has the working version. Home Assistant needs one restart to load a new `shell_command`.

## Writing a script that cleans up

The doorbell may lose your connection, your controller may restart, or two triggers may arrive at once. Three habits handle all of them, and [`tools/effect-template.sh`](../../tools/effect-template.sh) has each in about twenty lines:

- A watchdog. Every effect starts a detached timer that restores the normal state after a fixed time. Tested: the timer fires after the SSH session that started it has ended.
- One effect at a time. A new start stops the previous one, and only one restore runs. Tested.
- Checked kills. Scripts store the PID of a timer or effect in a file. PIDs get reused, so a stale number can name an unrelated process. Check `/proc/<pid>/cmdline` for your script's name before killing. Tested with a stale PID.

A related trap from the Halloween build: a timer that calls a function which first kills "the timer in the PID file" kills itself, because the timer is that process. Delete the PID file before calling the cleanup.

Write the restore step first and run it on its own before you build the effect. Make it safe to run twice.

## Go easy on the CPU

The doorbell runs near its limit. These measurements were taken during normal use:

- Reading the whole log costs about 0.4 seconds of wall time. A loop that does it every few seconds adds up; a `logread -f` stream is cheaper.
- A recursive `grep` over the filesystem ran for over 90 seconds, and the load average read 8.4 while it ran. Search copies of files elsewhere.
- Starting a program in a tight loop is the expensive part of a shell loop. A short `sleep` between steps is fine.

## Expect your settings to be overwritten

The NVR sends its own screen, sound and LED settings from time to time. In one case a change in Home Assistant was followed within a second by the NVR replacing a custom ring tone and deleting its file. Anything you keep in `ubnt_sounds_leds.conf` needs a check that notices when it is gone and puts it back. The Halloween example runs `sound_check` every two minutes; the command only writes when something is missing.

## After a reboot

A reboot clears `/tmp` and every timer. A script in `/etc/persistent` is still there, but nothing runs it. Plan for a controller that notices, for example a Home Assistant automation that runs a `check` command every few minutes and reinstalls what is missing. The Dropbear key file may also be cleared by a reboot; that was not tested.

## Before you rely on it

1. Run the restore command alone and confirm the device returns to normal.
2. Run the effect with someone watching and read `logread | tail` afterward; `statusCode 0` from `ubnt_ipc_cli` only means the message was delivered.
3. Start the effect twice in a row and confirm the second replaces the first.
4. Let the watchdog fire on its own, with the starting session closed.
5. Check the saved config under `/etc/persistent` after any settings change.
6. Keep the backups from the [quick start](quick-start.md) and know the [undo steps](undo-and-recovery.md).
