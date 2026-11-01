# G4 Doorbell Pro control reference

This is what controls what on a UniFi G4 Doorbell Pro (board G4R, system ID 0xa574, firmware 5.5.45) that a UniFi Protect NVR manages. Everything here was found on 2026-10-31 by sending a command and watching or listening to the hardware. Each claim carries one of three labels:

- seen: a person watched or listened and reported the result.
- logged: the doorbell's log or a register readback showed it.
- strings: read from the stock binaries with `strings`, not tried.

The device runs Linux 4.9.184 (aarch64) with BusyBox 1.37.0 and Dropbear 2020.81. Its services are `ubnt_sounds_leds` (lights, sounds, scene logic), `ubnt_lcm_gui` (screen), and `ubnt_mcu` with its agent (the microcontroller that owns the button ring). They talk to each other with `ubnt_ipc_cli`.

## Reaching the doorbell

The login is `ubnt`, which maps to uid 0. Password and key logins both work.

Dropbear reads `/etc/dropbear/authorized_keys`. When this was found it held one line, the Mac's key, in a directory with a 1999 timestamp, which suggests the file is created at boot; how it is built was not traced. A line added only to `/etc/persistent/.ssh/authorized_keys` was ignored (logged: the key was offered and rejected; the same line in the Dropbear file authenticated). The persistent file is on flash and survives reboots. The Dropbear file probably does not, so a key added there should disappear at the next reboot; no reboot was done to confirm it.

OpenSSH 10 clients need `-o HostKeyAlgorithms=ecdsa-sha2-nistp256`. Without it the doorbell drops the connection during key exchange, before any key is checked. Dropbear is started with `-r /etc/persistent/dropbear_ecdsa_host_key`.

Dropbear's binary contains the authorized_keys options `command="`, `no-port-forwarding`, `no-agent-forwarding` and `no-pty` (strings). A line with `command="sh /tmp/halloween.sh",no-port-forwarding,no-agent-forwarding,no-pty` authenticated and ran only that script: `restore` returned 0 and `id` returned the script's own "denied" with exit code 2 (logged). The binary has no string for `no-X11-forwarding`; the first attempt included it, and it was never tested alone.

`/tmp` is tmpfs and empty after a reboot. Scripts, converted sounds and timers placed there are gone. `/etc/persistent` is a 7.6 MB flash volume, 236 KB used at the start.

## Button ring

The ring is driven by the microcontroller, not by anything under `/sys/class/leds`. Setting `R` to 5% for three seconds, and pushing `userLedColorFg` through `ChangeSoundLedSettings`, changed nothing on the ring (seen, in the earlier session).

What works is the agent's `SetLEDStatus` call:

```sh
ubnt_ipc_cli -T=ubnt_mcu_agent -r=1 -t=2000 -m='{"functionName":"SetLEDStatus","mode":1,"fgColor":4,"bgColor":0,"bright":-1}'
```

The binary defines `mode` 0 to 6, `fgColor` and `bgColor` 0 to 15, `bright` -1 to 100, `breathingPeriodMs`, `breathingEndsMs`, and four `blinking*` timings (strings). There is no field for an LED index or position, so the whole ring takes one color. The ring keeps the last value until something replaces it.

Colors at `mode` 1, brightness 60 (seen, over three passes; the first reply named three colors for four codes, so some assignments are interpretation, and codes 7 and the white and light pink groups are the least certain):

| fgColor | Looked like |
|---|---|
| 1, 3 | red |
| 2, 7 | off |
| 4, 6 | blue |
| 5, 8 | pink |
| 9, 12, 14 | white |
| 10, 11, 13, 15 | light pink |

`fgColor 4`, `bright -1` is the stock look: after the test the viewer confirmed it matched how the ring normally appears.

Modes with red at brightness 60 and the timings 3000 ms breathing, 1200 ms blink period, 300 ms on and off (seen, from a list given in order): 1 and 5 solid, 2 nothing visible, 3 blinking, 4 pulsing, 6 not reported. Mode 4 is the hardware breathing mode.

Orange comes from a second source. The `G` channel of the LP5562 driver (`/sys/class/leds/G`, I2C address 2-0030) adds green to the ring. Red plus `G` at 25 looked orange, at 60 yellow, at 120 greenish yellow (seen). `R`, `B` and `W` showed nothing. The ring in mode 4 over `G` at 12 pulsed between green and orange, which the viewer picked for the Halloween idle effect. Nothing in the firmware strings explains why the ring's green is on the LP5562, and that was not investigated.

## Bottom spotlight

The spotlight is on the LM3644 driver (I2C 2-0063). Writing `/sys/class/leds/torch1/brightness` lit it at 10 of 127 (seen).

It lit unreliably until the driver's flag registers were read first. The command that failed three times in a row left register `0x01` at `0x01` (no torch mode) and the light stayed dark. After `i2cget -f -y 2 0x63 0x0a` and `0x0b`, a latched bit in `0x0b` (seen once as `0x02`) cleared, writes read back `0x09`, and three of three pulses lit (seen).

```sh
i2cget -f -y 2 0x63 0x0a; i2cget -f -y 2 0x63 0x0b
echo 10 > /sys/class/leds/torch1/brightness
```

Only `torch1` was confirmed. `torch`, `torch2` and the `flash` channels were not isolated. Higher levels, heat and the stock night glow (`glow.mode personInFrontActivated`, `activeAt night`, which probably uses the same LED) were not tested.

## Screen

### Custom animations

`ubnt_lcm_gui` reads `/etc/persistent/ubnt_lcm_gui.conf`. Its `customAnimations` list maps a screen name (`guiId`) to a sprite file in `/etc/persistent/lcm/animation/`. Each entry has `file`, `count`, `durationMs`, `loop` and `enable`. The file on disk is `<file>.anim` and is a plain PNG, with a 32-character `<file>.md5` next to it.

The stock welcome sprite is 240 by 240. The stock ringing sprite is a horizontal strip of 48 frames at 130 pixels wide. The Halloween sprites are 1920 by 240, eight 240-pixel frames side by side, quantized to 128 colors; each file is about 195 KB.

Apply a change by sending it to the service:

```sh
ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=4000 -m='{"functionName":"ChangeLcmGuiSettings","customAnimations":[{"guiId":"WELCOME","file":"halloween-welcome.png","count":8,"durationMs":2000,"loop":true,"enable":true}]}'
```

The service merges entries by `guiId`. Sending a list without an entry does not remove it (logged: after a "restore" call that listed only `WELCOME`, the saved file still held the `WAITING_FOR_RESPONSE` override). Disable an override by sending its entry again with `"enable":false`.

The names that matter here are `WELCOME` (idle) and `WAITING_FOR_RESPONSE` (the "Ringing" screen after a press). `TALKING` appears while audio plays through the speaker and is a separate screen.

### Keeping the screen on

About 40 seconds after a person leaves, the doorbell logs `LCM brightness: 0 (Auto-off active)` and the screen goes dark. `screenOffTimeout` in `ubnt_sounds_leds.conf` is `auto`; the binary accepts `auto`, `15`, `30` and `60`, and ten other values tried (`never`, `always`, `off`, `1h`, `3600` and others) each fell back to `auto`; nine logged `Invalid screenOffTimeout value` and one logged nothing. The longest setting is one minute.

A loop on the doorbell can hold the image instead. It checks the log every four seconds and, when the last brightness line says auto-off, sends:

```sh
ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m='{"functionName":"ShowGui","guiId":"WELCOME","welcomeType":"image","brightness":60}'
```

The screen stayed lit from 7:02:49 PM until the end of the observation, and the viewer confirmed it was still on later (seen). A person walking past may still blank it for up to four seconds, because the stock logic runs first.

The stock `doorbell_mcu_control lcm_off` script turns the screen off with `ShowGui` and `"brightness":0` (strings). The `stock` path that sends it ran once in a timer test and the call went out; nobody watched the screen.

## Ring sound

The ring tone is a `customSounds` entry in `/etc/persistent/ubnt_sounds_leds.conf`:

```json
{"enable":true,"file":"halloween-ring.ogg","repeatTimes":1,"soundStateName":"RING_BUTTON_PRESSED","volume":35}
```

The file goes in `/etc/persistent/sounds/` with a `.md5` file beside it. Send only the `customSounds` key to apply it. A full copy of the saved config was rejected, and the rejection (`Animation, lit/blink and Breathing parameters couldn't be used at the same time`) still came back with `statusCode 0`.

On the first press the service converts the Ogg to a 16 kHz mono WAV with sox, writes it to `/tmp`, and plays it. The log showed the press at 18:51:17, the conversion done at 18:51:18, and the ring screen cleared at 18:51:21. The viewer called the first press a large delay (seen). Later presses use the cached WAV; a press after the cache is deleted pays the conversion again. A second press was not timed.

ffmpeg's built-in Vorbis encoder only writes stereo files. The stereo file converted and played.

## What UniFi Protect overwrites

The NVR pushes its saved settings to the doorbell at times not controlled here. One push was observed, and the cause is inferred from timing: `volume_set` through Home Assistant at 18:46:57 was followed within a second by the custom sound entry reverting to `Default.ogg` at volume 100, and `halloween-ring.ogg` and its `.md5` being deleted (logged: `WAV cache file does not exist` from the custom-files handler). The screen config (`ubnt_lcm_gui.conf`) was not touched by that push.

Anything stored in `ubnt_sounds_leds.conf` needs a check that runs on a timer and puts it back. `sound_check` in `doorbell/halloween.sh` does that with a master copy in `/tmp`.

## What did not work

- `GetSoundLedSettings`, `GetLEDStatus`, `GetState`: the sound service answers `Operation not supported`.
- `ChangeSoundLedSettings` with `userLed*` fields: no visible change on the ring, with `statusCode 0`.
- `R`, `B`, `W` under `/sys/class/leds`: no visible effect at brightness 150.
- `PlayFile`: accepted by the sound service with `statusCode 0` for four different file arguments; no sound, no log line. The name `fileName` sits next to `ToFCalibrationControl` in the binary's strings, so it probably belongs to the distance sensor.
- `media_player.play_media`, first try: with no `announce` flag and the volume at 20%, Home Assistant accepted it and nothing was heard. The second try, with `announce: true` at 50%, played. Which of the two changes mattered was not isolated.
- Raw SPI: `/dev/spidev1.1` exists (device tree `ambarella,spidev`). Nothing was written to it because the attached chip is unknown.

## Things worth knowing on the Home Assistant side

- The UniFi Protect integration's event entities hold a timestamp as state. `event.g4_doorbell_pro_doorbell` read `unknown` until the first ring after a restart. A trigger condition that rejects a change from `unknown` drops that first event.
- `media_player.g4_doorbell_pro_speaker` reported `volume_level 1.0`. Changing it triggered the Protect push above.
- Playing audio through that speaker switches the screen to the stock `TALKING` image for the length of the clip.
- `shell_command` runs inside the Home Assistant core container with OpenSSH 10.3. A new `shell_command` domain needs a restart; reload returns 400.
- The SSH add-on's root shell is zsh, which does not split an unquoted `$VARIABLE` into words. A command like `ssh $OPTS host` fails there with the whole string read as one option.
- LIFX bulbs running a custom effect started in the LIFX app overwrote Home Assistant's colors within about three seconds. `light.turn_on` with `effect_stop` and `lifx.effect_stop` did not end it; stopping it in the app did.

## Reading the logs

```sh
logread | grep -E "soundled|ubnt_lcm_gui|ubnt_mcu_agent" | tail -40
```

Useful lines: `Enqueued 'RING_BUTTON_PRESSED'` (a press), `State transition: ... TALKING` (audio through the speaker), `LCM brightness: N` and `Auto-off active` (screen), `Successfully converted ... to /tmp/...wav` (ring sound), `Scene state PERSON_IN_FRONT_ACTIVATED` (the stock detection scene), and `Invalid screenOffTimeout value` (a rejected setting).
