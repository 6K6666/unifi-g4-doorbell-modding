# LED, sound and screen control

In short: the ways Ubiquiti's own tools drive the ring, the sounds and the screen, with what has and has not been tried here. Read this when the recipes do not cover what you want.

How the ring, the sounds and the screen are meant to be driven, with the recipes from the firmware's own factory scripts next to what was verified on a real doorbell. The factory scripts are the closest thing to documentation: `test_led_behavior.sh`, `testLed.sh`, `playSound.sh` and `buzzer_sounds.sh` in `/usr/local/bin` and `/usr/bin`. Labels are explained in the [system map](system-map.md). Entries marked "stock script" have not been run here.

## Three ways to light the ring

| Path | What it is | Status |
|---|---|---|
| `SetLEDStatus` to `ubnt_mcu_agent` | direct command to the ring's microcontroller: one color, brightness, and a mode (None, On, Off, Blink, Breathing, FadeOnOff, FadeOffOn) | run and seen; see the [control reference](verified-controls.md) |
| `ChangeSoundLedSettings` to `ubnt_sounds_leds` | the "LED face" settings: color names, blink, breathing, a rotating animation | stock script; the two earlier attempts did not work, see below |
| sysfs `/sys/class/leds/G` | adds green through the LP5562 driver; with red from the first path it gives orange and yellow | run and seen |

The factory LED script `testLed.sh` is for the PoE doorbell (system ID 0xa575), which has a KTD2061 RGB driver with LEDs named A1 to C2. Reading the script, a 0xa574 unit falls through to the last case and prints "none support sysid"; if it did get past that, it exits when no `ktd2061` node exists. It cannot be used here.

## LED-face recipes from the stock script

`test_led_behavior.sh` plays 21 named behaviors through `ChangeSoundLedSettings`. It prepares the device first:

1. `PlayState` with `name` `CONTROLLER_CONNECTED`
2. `ChangeSoundLedSettings` with `ledFaceAlwaysOnWhenManaged` 1 and `ledFaceEnabled` 1
3. It pauses the smart-detect process (`pkill -STOP smart`) so detection events do not change the ring. Doing that stops detection and recording analytics while it lasts; it is not a good idea on a doorbell that is in use.

Two earlier attempts to set the ring this way do not count as tests. A payload from a previous session mixed `userLedBlinkPeriodMs` and `ledBreathingPeriodMs` in a copy of the whole config. A message sent at 18:04 (`userLedOnNoff`, `userLedColorFg`, `userLedColorBg`, `userLedBlinkPeriodMs` 0) was followed in the log by `Animation, lit/blink and Breathing parameters couldn't be used at the same time`, and the ring stayed as it was (logged and seen). The saved config already had `ledFaceEnabled` and `ledFaceAlwaysOnWhenManaged` at 1, so step 2 was already in effect. Nobody has sent the stock script's exact sequence: `PlayState` `CONTROLLER_CONNECTED`, then a lit-only message with no background color. It is also not established that the LED face is the ring on this board.

The color names the script uses are `white`, `blue`, `red`, `green`, `amber` and `black`. The behaviors, as payload fields on `ChangeSoundLedSettings`:

| Behavior | Fields |
|---|---|
| Steady color | `userLedColorFg` = color, `userLedOnNoff` 1, `userLedBlinkPeriodMs` 0 |
| Off | `userLedColorFg` `black`, `userLedOnNoff` 1, `userLedBlinkPeriodMs` 0 |
| Breathing | `userLedColorFg` = color, `ledBreathingPeriodMs` = 2000 (white) or 3000 (blue, green) |
| Blinking on and off | `userLedColorFg`, `userLedOnNoff` 1, `userLedBlinkPeriodMs` = 125 (strobe), 250 (rapid), 1000 (slow), 2000 (amber) |
| Alternating two colors | `userLedColorFg`, `userLedColorBg`, `userLedOnNoff` 1, `userLedBlinkPeriodMs` 1000 |
| Rotating | `ledAnimColorFg`, `ledAnimColorBg` `black`, `ledAnimDensity` 25, `ledAnimOnDurationMs` 83 |
| Flash twice | off, then blink at 200 ms for 350 ms, then off |

Send one family at a time. The service logs `Animation, lit/blink and Breathing parameters couldn't be used at the same time` when a message mixes them (logged).

Three details matter: `amber` exists as a named color, the rotating animation lights a moving part of the ring (density 25 is presumably the share of the ring that is lit), and breathing is available in any color. The microcontroller path in the control reference tried all 16 color codes. They looked red, blue, pink, white and light pink to the viewer, and none looked amber.

## Screens

The stock GUI table for this board defines 49 screen ids; [lcm-screens.txt](data/lcm-screens.txt) lists them. The ones that matter for customizing:

| Screen | Stock content | Notes |
|---|---|---|
| `WELCOME` | `Welcome_Anim_60.lcmi`, no text | idle image; replaced by a `customAnimations` entry |
| `WELCOME_TEXT` | "Welcome" over `Welcome.png` | named in the screen log after one wake |
| `WAITING_FOR_RESPONSE` | "Ringing" over `Ringing_Anim_48.png` | after a button press |
| `TALKING` | "Talk" over `Talking_Anim_48.png` | while audio plays through the speaker, including audio sent from Home Assistant |
| `RESTARTING`, `UPDATING_FIRMWARE`, `POOR_WIFI_SIGNAL`, `INSUFFICIENT_POWER` | system warnings | keep these stock |

`ShowGui` with a `guiId` and `brightness` shows any of them (run). A custom animation replaces the sprite for one `guiId`; see the [control reference](verified-controls.md) for the file format and the merge behavior. The 240 by 240 LCD is also framebuffer `fb2`; drawing to it directly was not tried.

## Sounds

Four routes, from the firmware's perspective:

| Route | How | Status |
|---|---|---|
| Ring tone | a `customSounds` entry for `RING_BUTTON_PRESSED` in `ubnt_sounds_leds.conf`, with the file in `/etc/persistent/sounds/` | run and heard; the NVR can overwrite it |
| Named state | `PlayState` with a state name | stock script uses it once; the firmware has 134 state names in [play-states.txt](data/play-states.txt), grouped as greetings, door and NFC results, emergency modes, Wi-Fi setup, power and thermal events, and the ring and talk states |
| Local file playback | `/usr/local/bin/playSound.sh FILE [-v 0-100]`: plays `.ogg` with `play -v` (volume 0 to 1) and `.wav` with `aplay --volume` | stock script; `play`, `aplay`, `sox` and `amixer` are installed. Whether the speaker amplifier is on without the sound service is not known |
| Buzzer | `buzzer_sounds.sh` drives a PWM buzzer at `/sys/class/pwm/pwmchip9/pwm0` | stock script; that path does not exist on this unit |

Audio sent through Home Assistant's `media_player` is a fifth route. It plays, but the screen switches to the stock `TALKING` image. A volume change on the player was followed within a second by the NVR's settings replacing a custom ring tone (logged; the cause is inferred from timing).

Stock tones for this board in `/usr/etc/sounds/0xa574/`: `chime.ogg`, `denied.ogg`, `errorConnect.ogg`, `launchApp.ogg`, `resetDefaults.ogg`, `setupComplete.ogg`, `success.ogg`, `systemInit.ogg`.

Two state names suggest audio-reactive lighting: `MIC_TO_LED` and `SNDOUT_TO_LED`. The binary has a pulse-input reader (strings). Nothing here shows how to start either.

## Not tried yet

Each of these has a concrete test, listed here so someone can pick one up:

- the stock script's exact sequence (`PlayState` `CONTROLLER_CONNECTED`, then lit-only messages for amber, breathing and the rotating animation, one family per message)
- `PlayState` with a state that has a short sound, and `playSound.sh` with a small `.ogg`
- `ShowSimpleScreen` and `PushGui`
- a listener (`ubnt_ipc_cli -l`) during a button press, to record the event names in order
