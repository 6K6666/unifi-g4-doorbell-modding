# Quick start: your first changes

Risk: low. These steps change the ring, spotlight and screen only. Nothing is saved to the doorbell, and every step has an undo.

This walks you through changing the doorbell's ring color, turning on its spotlight and switching its screen. It takes about twenty minutes and needs one person at the doorbell to watch.

## Before you start

- SSH access to the doorbell. If `ssh ubnt@DOORBELL_IP` says "connection refused", start with [getting SSH access](../getting-started/getting-ssh-access.md).
- The doorbell's address, in place of `DOORBELL_IP` in every command. Protect shows it on the doorbell's settings page, and your router lists it among its connected devices.
- A terminal on a computer on the same network.

Every command here was run on a real doorbell (G4 Doorbell Pro, firmware 5.5.45) and the result was watched. None of them touch recording, notifications or the indoor chime. Another firmware version may behave differently.

## Two places you will type commands

Each code block starts with a line saying where to run it:

- On your computer: the terminal you opened, before you log in.
- On the doorbell: after you log in with `ssh`. The prompt changes, and your commands now run on the doorbell itself. Stay logged in for steps 3 to 6.

Pasting a doorbell command into your own computer's terminal does nothing useful, and pasting `ssh` into the doorbell's shell starts a second login. If you are unsure, look at the prompt.

## Step 1: save the stock settings

Back up first, so you can put things back.

On your computer:

```sh
ssh ubnt@DOORBELL_IP 'tar czf - -C / etc/persistent/ubnt_lcm_gui.conf etc/persistent/ubnt_sounds_leds.conf etc/persistent/lcm etc/persistent/sounds' > doorbell-settings-backup.tgz
```

Keep that file somewhere safe. It holds your screen and sound settings. Do not archive all of `/etc/persistent`; it also holds the doorbell's SSH key and certificates.

## Step 2: log in and look around

On your computer:

```sh
ssh ubnt@DOORBELL_IP
```

Enter the recovery code or use your key. You are now on the doorbell. Nothing in this step changes anything.

On the doorbell:

```sh
grep -E 'sysid|name' /etc/board.info   # model and board ID
df -h                                  # disk space; / is full and read-only, that is normal
logread | tail -20                     # the doorbell's recent log
```

The doorbell has little spare CPU and memory. Keep commands small, and do not run searches across the whole disk (see [exploring safely](../getting-started/exploring-safely.md)).

## Step 3: change the ring color

The button ring is controlled by a small separate chip. Send it one color for the whole ring.

On the doorbell:

```sh
ubnt_ipc_cli -T=ubnt_mcu_agent -r=1 -t=2000 -m='{"functionName":"SetLEDStatus","mode":1,"fgColor":1,"bgColor":0,"bright":60}'
```

The ring should turn red. Try the other color codes by changing `fgColor`:

| fgColor | Looks like |
|---|---|
| 1 | red |
| 4 | blue (the normal look) |
| 5 | pink |
| 9 | white |
| 0 | off (also set `"bright":0`) |

The ring cannot make green, orange or purple by itself. Orange is red plus a little green from a second light driver. With the ring red, run this on the doorbell:

```sh
echo 25 > /sys/class/leds/G/brightness
```

The ring turns orange; try 60 for yellow. To make the ring pulse instead of stay solid, change `"mode":1` to `"mode":4` and add `"breathingPeriodMs":3000`.

Undo, on the doorbell, which puts the ring back to its normal look:

```sh
echo 0 > /sys/class/leds/G/brightness
ubnt_ipc_cli -T=ubnt_mcu_agent -r=1 -t=2000 -m='{"functionName":"SetLEDStatus","mode":1,"fgColor":4,"bgColor":0,"bright":-1}'
```

In testing the ring kept whatever you last set until another command arrived. A button press or a person at the door may change it sooner.

## Step 4: turn on the spotlight

The light under the screen is a torch driver. It needs one trick: read two of its status registers first, or it sometimes ignores you.

On the doorbell:

```sh
i2cget -f -y 2 0x63 0x0a
i2cget -f -y 2 0x63 0x0b
echo 10 > /sys/class/leds/torch1/brightness
```

The light comes on. The value is out of 127, and 10 is bright enough to see. Turn it off, on the doorbell:

```sh
echo 0 > /sys/class/leds/torch1/brightness
```

Do not leave it on for hours until you have checked the temperature on your own unit. Heat and higher brightness levels were not tested.

## Step 5: show a different screen

The screen shows the idle picture normally and a "Ringing" animation after a button press. You can show either on demand.

On the doorbell:

```sh
ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m='{"functionName":"ShowGui","guiId":"WAITING_FOR_RESPONSE","brightness":80}'
```

Put the idle picture back, on the doorbell:

```sh
ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m='{"functionName":"ShowGui","guiId":"WELCOME","welcomeType":"image","brightness":60}'
```

The screen goes dark by itself about 40 seconds after someone leaves. That is normal.

## Step 6: undo everything

If anything looks wrong, run all of these on the doorbell. They are safe to run when nothing has changed:

```sh
echo 0 > /sys/class/leds/G/brightness
echo 0 > /sys/class/leds/torch1/brightness
ubnt_ipc_cli -T=ubnt_mcu_agent -r=1 -t=2000 -m='{"functionName":"SetLEDStatus","mode":1,"fgColor":4,"bgColor":0,"bright":-1}'
ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m='{"functionName":"ShowGui","guiId":"WELCOME","welcomeType":"image","brightness":60}'
```

Type `exit` to leave the doorbell's shell. [Undo and recovery](undo-and-recovery.md) covers the other things this repository changes: custom screens, custom ring tones and SSH keys.

## What not to try yet

- Do not send a whole saved config file back to the doorbell. It rejects some fields and still reports success.
- Do not run the scripts in `/usr/bin` or `/bin` whose names contain `upgrade`, `account` or `persist` without reading them first. They flash chips or change logins.
- Do not write to `/dev/spidev1.1`, the MTD devices, or run the `i2c_access` tools on other addresses. They bypass the drivers.

## Where next

- To change what the screen shows or what the ring plays: [recipes](recipes.md)
- To run your own script, on a timer or from Home Assistant: [running custom scripts](running-custom-scripts.md)
- To see everything built from these pieces: [the Halloween example](../../examples/halloween-2026/README.md)
