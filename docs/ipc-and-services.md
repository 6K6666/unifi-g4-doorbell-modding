# IPC and services

The doorbell's services talk to each other through a local message bus, and `ubnt_ipc_cli` puts a message on it from the shell. Nearly everything controllable on the device is reached this way. Labels are explained in the [system map](system-map.md).

## Sending a message

```sh
ubnt_ipc_cli -T=<target> -r=1 -t=2000 -m='{"functionName":"<Name>", ...}'
```

Options from the tool's own help:

| Option | Meaning |
|---|---|
| `-T`, `--to` | target service, for example `ubnt_sounds_leds` |
| `-m`, `-M` | message as inline text, or as a file |
| `-r=1` | wait for a response; without it the call returns at once |
| `-t` | timeout in milliseconds, default 10000 |
| `-x` | print only one field of the response, for example `-x=response/payload` |
| `-s`, `-z` | quieter logging; no logging |
| `-b` | broadcast to every service that listens (used for events) |
| `-q` | queue the message if the target is not running |
| `-n`, `-p` | function name and path parameters: `-p='video.name=x'` sets a value, `-p='video.vin.0.video1.fps'` reads one. Not tried here |
| `-l` | run a listener that prints messages matching a regular expression |

A response looks like this (fields trimmed):

```json
{"request":  {"from": "ubnt_ipc_cli_123", "functionName": "...", "to": "ubnt_sounds_leds", "responseExpected": true},
 "response": {"functionName": "__response__", "statusCode": 0, "payload": null}}
```

`statusCode` is 0 when the target accepted the message, and 1 for an unsupported one, with the payload `Operation not supported`. Zero means the message was well formed and delivered. It does not mean the settings took effect: a full copy of the saved sound config returned `statusCode 0` while the service logged that it rejected it (logged).

Targets seen in use: `ubnt_sounds_leds`, `ubnt_lcm_gui`, `ubnt_mcu_agent`, `ubnt_ctlserver`, `ubnt_avclient`, `ubnt_networkd`. The tool reads its list of valid targets from an endpoints file; the path is unknown.

## How a setting reaches a service

```
Protect NVR  ->  ubnt_avclient  ->  ubnt_lcm_gui, ubnt_sounds_leds, ubnt_ctlserver, ubnt_networkd, ...
local web UI ->  lighttpd -> ubnt_cgi  ->  the same services
a shell      ->  ubnt_ipc_cli           ->  the same services
```

`ubnt_avclient` accepts the `Change...Settings` family and appears to pass each to its owner, including `ChangeLcmGuiSettings` and `ChangeSoundLedSettings` (strings). That is why a setting pushed from the NVR overwrites one set by hand. A hand-made change goes straight to the service, and the controller's own copy of the setting is unchanged.

## Calls run during this project

| Target | Message | Result |
|---|---|---|
| `ubnt_mcu_agent` | `SetLEDStatus` with `mode`, `fgColor`, `bgColor`, `bright`, `breathingPeriodMs` | drives the button ring (seen); details in the [control reference](g4-doorbell-pro-control-reference.md) |
| `ubnt_sounds_leds` | `ChangeSoundLedSettings` with only `customSounds` | installed a custom ring tone (logged and seen) |
| `ubnt_sounds_leds` | `ChangeSoundLedSettings` with `screenOffTimeout` | accepted `auto`, `15`, `30`, `60`; anything else fell back to `auto` and logged why (logged) |
| `ubnt_sounds_leds` | `ChangeSoundLedSettings` with `userLedOnNoff`, `userLedColorFg`, `userLedColorBg`, `userLedBlinkPeriodMs` | ring unchanged (seen); the log recorded that lit, blink, animation and breathing parameters cannot be used together, so the service rejected it (logged); see the [recipes](led-sound-and-screen-control.md) |
| `ubnt_sounds_leds` | `GetSoundLedSettings`, `GetLEDStatus`, `GetState`, `GetSoundLedState` | `Operation not supported` |
| `ubnt_sounds_leds` | `PlayFile` with `file`, then with `fileName` (relative and absolute path) | `statusCode 0`, no sound, no log line; the argument shape is unknown |
| `ubnt_lcm_gui` | `ChangeLcmGuiSettings` with `customAnimations` | installed both Halloween screens (seen as "the normal one and one that is winking") |
| `ubnt_lcm_gui` | `ShowGui` with `guiId` and `brightness` | shows a screen and wakes the display (seen) |
| `ubnt_lcm_gui` | `ShowGui` with `brightness` 0 | call sent; whether the screen went dark was not watched |

## Calls found in the firmware's own scripts

Not run here. Argument shapes are as written in the scripts.

| Target | Message | Where used |
|---|---|---|
| `ubnt_sounds_leds` | `PlayState` with `name` (`CONTROLLER_CONNECTED`) | the LED test script, to put the device in a known state |
| `ubnt_sounds_leds` | `ChangeSoundLedSettings` with `ledFaceEnabled`, `ledFaceAlwaysOnWhenManaged` | same script |
| `ubnt_sounds_leds` | `ChangeSoundLedSettings` with `userLedColorFg`, `userLedColorBg`, `userLedOnNoff`, `userLedBlinkPeriodMs`, `ledBreathingPeriodMs`, `ledAnimColorFg`, `ledAnimColorBg`, `ledAnimDensity`, `ledAnimOnDurationMs` | same script; the [recipes](led-sound-and-screen-control.md) list each combination |
| `ubnt_lcm_gui` | `ShowGui` with `guiId` `RESTARTING` and `brightness` 80 | the reboot path |
| `ubnt_ctlserver` | `SaveToFlash` | `ubnt_cmd_persist.sh` |
| `ubnt_ctlserver` | `Reboot`, `RefreshAccelerometer` | maintenance scripts |
| `ubnt_avclient` | `SoftRestart`, with `-f=ubnt_avclient` | `ubnt_cmd_reload_avclient.sh` |
| `ubnt_networkd` | `NetworkStatus`, with `-x=response/payload/ipAddress` | network scripts |
| every service | `EventUpdateFirmwareStatus` broadcast with `status` `FW_UPDATING` | firmware update scripts |

## What each service accepts

[docs/data/ipc-names.txt](data/ipc-names.txt) lists every message name found in 19 service binaries, split into commands and events. The lists are names only, taken with `strings`. A name in a binary does not show that the service handles it on this board. Highlights worth trying first:

| Service | Interesting names |
|---|---|
| `ubnt_sounds_leds` | `PlayState`, `PlayBuzzer`, `PlayFile`, `StartLedBlink`, `StopLedBlink`, `SetWifiStatusLed`, `SetToFRange`, `CustomSoundsOperation`, `ResetSoundLedSettings`, `SetThermalProtectionMode` |
| `ubnt_lcm_gui` | `ShowGui`, `PushGui`, `ShowSimpleScreen`, `ChangeLcmGuiSettings` |
| `ubnt_avclient` | `PlayWav`, `PlayBuzzer`, `SetChimeDuration`, `SetIRZonePct`, `SetToFRange`, `GetIlluminance`, `GetThermometerValue`, `ShowGui`, `StartLedBlink`, `SetLEDStatus` |
| `ubnt_ispserver` | `SetICR` (infrared cut filter), `GetIlluminance`, `GetSensorTemperature`, `ResetIspSettings` |
| `ubnt_ctlserver` | `SaveToFlash`, `GetThermalProtectLevel`, `SetThermalProtectionMode`, `GetSystemStats`, `GetMcuDebugInfo`, `GetTimezone` |
| `ubnt_networkd` | `GetWiFiInfo`, `RestartNetwork`, `StartPairing`, `RemoveWiFiSettings` |
| `ubnt_nfc`, `ubnt_access`, `ubnt_fingerprint` | `ChangeNfcSettings`, `ChangeAccessSettings`, `EnrollFingerprint`, `DeleteAllFingerprints` |
| `ubnt_uahubl2` | `UnlockDoor`, `UnlockPeriod`, `SendCallDoorBell`, events `EventCallDoorBell`, `EventPushBtnNotify` |

Events are broadcast notices such as `EventRingButtonPressed` (named in `ubnt_ctlserver`), `EventSmartDetectPersonInFront` (named in `ubnt_fingerprint`) and `EventColorNightVisionStatus`. A listener started with `ubnt_ipc_cli -l` is the way to watch them live; that was not tried.

## Messages that change a lot at once

Do not send these casually:

- `Reboot`, `ResetToDefaults`, `ResetDeviceSettings` (`ubnt_ctlserver`), `ResetUsrPwd`, `UpdateFirmwareRequest`
- `ChangeUsernamePassword`, `EnableUsernamePassword`, `DisableUsernamePassword`
- `DeleteAllFingerprints`, `RemoveWiFiSettings`, `ResetLcmGuiSettings`, `ResetSoundLedSettings`
- `StartService` and `StopService`, which appear to switch init entries (see the system map)
