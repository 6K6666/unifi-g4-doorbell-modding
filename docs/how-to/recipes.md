# Recipes

Risk: medium. The picture and ring tone recipes write small files and settings to the doorbell's saved storage, and the undo for each is listed. The others change the ring, spotlight or screen only while they run.

Short, copy-and-adapt recipes for the modifications that work. Each lists what it does, the steps, how to undo it and how well it has been tested. Replace `DOORBELL_IP` with your doorbell's address. Reference details live in [LED, sound and screen control](../reference/led-sound-and-screen-control.md) and [verified controls](../reference/verified-controls.md).

If you have not changed anything on the doorbell yet, do the [quick start](quick-start.md) first.

## A custom welcome picture

Replace the idle screen with your own picture or short animation.

1. Make the frames. This code is adapted from the script that made the Halloween pictures. Each frame is 240 by 240 pixels. Put the frames side by side in one PNG, left to right, so eight frames give a 1920 by 240 image. The Halloween picture used 8 frames, 128 colors, about 195 KB.

   ```python
   from PIL import Image
   frames = [Image.open(f"frame-{i}.png").convert("RGB").resize((240, 240)) for i in range(8)]
   strip = Image.new("RGB", (240 * 8, 240))
   for i, f in enumerate(frames):
       strip.paste(f, (240 * i, 0))
   strip.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save("mypic.png.anim", format="PNG", optimize=True)
   ```

2. Copy it to the doorbell with a checksum file. `scp` needs `-O`:

   ```sh
   scp -O mypic.png.anim ubnt@DOORBELL_IP:/etc/persistent/lcm/animation/
   ssh ubnt@DOORBELL_IP 'cd /etc/persistent/lcm/animation && md5sum mypic.png.anim | cut -d" " -f1 | tr -d "\n" > mypic.png.md5'
   ```

3. Tell the screen service to use it for the idle screen. `file` is the name without `.anim`, and `count` is the number of frames:

   ```sh
   ssh ubnt@DOORBELL_IP 'ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=4000 -m='\''{"functionName":"ChangeLcmGuiSettings","customAnimations":[{"guiId":"WELCOME","file":"mypic.png","count":8,"durationMs":2000,"loop":true,"enable":true}]}'\'''
   ```

   Use `"guiId":"WAITING_FOR_RESPONSE"` instead to replace the "Ringing" screen after a button press.

Undo: send the same message with your entry set to `"enable":false`, and the original entry back (the file name for the stock picture is in your backed-up `ubnt_lcm_gui.conf`). Removing an entry from the list does not remove it; the doorbell merges by `guiId`.

Tested: both pictures in the Halloween example were installed this way and showed on the screen.

## A custom ring tone

Play your own sound when someone presses the button.

1. Make the sound. Keep it short, a few seconds. The doorbell converts it on the first press, which took about a second in the log; the viewer reported a longer delay, and later presses were not timed. ffmpeg's built-in Vorbis encoder writes stereo, and stereo works:

   ```sh
   ffmpeg -i mysound.wav -strict -2 -codec:a vorbis -ar 44100 -ac 2 -q:a 5 myring.ogg
   ```

2. Install the file with its checksum and point the ring-button state at it. Send only the `customSounds` key:

   ```sh
   scp -O myring.ogg ubnt@DOORBELL_IP:/etc/persistent/sounds/
   ssh ubnt@DOORBELL_IP 'cd /etc/persistent/sounds && md5sum myring.ogg | cut -d" " -f1 | tr -d "\n" > myring.ogg.md5'
   ssh ubnt@DOORBELL_IP 'ubnt_ipc_cli -T=ubnt_sounds_leds -r=0 -t=4000 -m='\''{"functionName":"ChangeSoundLedSettings","customSounds":[{"enable":true,"file":"myring.ogg","repeatTimes":1,"soundStateName":"RING_BUTTON_PRESSED","volume":35}]}'\'''
   ```

3. Press the button and listen.

Undo: send the same message with `"file":"Default.ogg"` and `"volume":100`.

The NVR can undo this for you. Keep a copy of your sound in `/tmp` or on your own machine, and check from time to time that the file and the setting are still there; the [custom scripts guide](running-custom-scripts.md) shows how. If the sound is gone, the stock tone plays and visitors still hear a ring.

Tested: installed and heard on a real press. The NVR removed it once. A check command reinstalled it after the file was deleted on purpose; that check has not repaired a change the NVR made itself.

## Keep the screen on

The screen turns itself off about 40 seconds after someone leaves. The doorbell's own timeout setting stops at 60 seconds, so a script has to wake it. This one checks the log every four seconds and wakes the screen when it sees the screen was switched off:

```sh
while true; do
  logread | grep "LCM brightness" | tail -1 | grep -q "Auto-off active" &&
    ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m='{"functionName":"ShowGui","guiId":"WELCOME","welcomeType":"image","brightness":60}'
  sleep 4
done
```

Run it inside a script with an end time and an off switch, not in a bare loop (see the [effect template](../../tools/effect-template.sh)). The log check costs about 0.4 seconds of wall time on a busy doorbell; a `logread -f` stream would be lighter.

Undo: stop the script, then `ShowGui` with `"brightness":0` and no `guiId`. That last command was sent once and the screen was not watched.

Tested: the screen stayed lit through the rest of the evening with the watcher running, and the viewer confirmed it was still on.

## A glowing or pulsing ring

Orange and a pulse need two light sources: the ring chip for red, and a second driver for green. See [quick start step 3](quick-start.md#step-3-change-the-ring-color) for the commands. The pulse the Halloween show used is mode 4 with a period of 3000 ms and green at 12:

```sh
echo 12 > /sys/class/leds/G/brightness
ubnt_ipc_cli -T=ubnt_mcu_agent -r=0 -t=1500 -m='{"functionName":"SetLEDStatus","mode":4,"fgColor":1,"bgColor":0,"bright":60,"breathingPeriodMs":3000,"breathingEndsMs":0}'
```

Undo: green back to 0 and the stock blue from the quick start.

Tested: red pulse over a little green, picked by eye from three variants.

## A candle-flicker spotlight

Step the torch level quickly, then hold. Read the status registers first, as in the quick start:

```sh
i2cget -f -y 2 0x63 0x0a; i2cget -f -y 2 0x63 0x0b
for l in 4 14 8 16 10 12; do echo $l > /sys/class/leds/torch1/brightness; sleep 0.25; done
echo 10 > /sys/class/leds/torch1/brightness
```

Undo: `echo 0 > /sys/class/leds/torch1/brightness`. Put a time limit on any script that turns it on.

Tested: the routine lit the spotlight in both previews.

## Read what the doorbell is doing

Safe, read-only:

```sh
cat /sys/bus/iio/devices/iio:device0/in_illuminance_input   # ambient light in lux
logread | grep -E "RING_BUTTON|Scene state" | tail          # recent button and person-in-front events
```

A button press sends your normal notification and rings the indoor chime, so test with someone's consent.

## Not working yet

These have been tried or read about but not made to work, so no recipe exists:

- Playing a sound file from the shell. `PlayFile` returns success and does nothing. The stock `playSound.sh` exists and has not been run.
- Setting the ring through the "LED face" messages (colors by name, amber, a rotating animation). See [LED, sound and screen control](../reference/led-sound-and-screen-control.md#led-face-recipes-from-the-stock-script).
- Lighting individual LEDs in the ring. The ring chip takes one color for the whole ring.
