# Halloween 2026: Haunted Witch Cat

Armed 6:53 PM MDT on October 31, 2026. Expires 2026-11-01 00:00 America/Denver (epoch 1793512800). The request is in [SPEC.md](SPEC.md). How the doorbell is controlled is in [the control reference](../docs/g4-doorbell-pro-control-reference.md), and what broke while building this is in [the build and review](../docs/halloween-2026-build-and-review.md).

## What a visitor sees

Idle: the three driveway bulbs trade dim purple and orange every seven seconds at 122 of 255, the front door holds amber at 120, the button ring pulses between green and orange, and the screen shows the blinking cat.

| Step | Lights | Doorbell |
|---|---|---|
| Driveway camera sees a person | Orange wave: bulb 1, 2, 3, front door, one second apart | nothing |
| Doorbell sees a person | Front door amber at 200 | Ring pink then orange, spotlight flickers then holds, back to idle after 30 s |
| Button pressed | Two red heartbeat pulses on the driveway bulbs, then three orange and purple swaps; front door steady at 180 | Ring sound with meow and cackle at 35%, cat ringing screen, ring red then orange and pink, spotlight on |
| 8 s after the show ends | Back to idle | Ring pulse resumes, spotlight off |

Cooldowns: 45 seconds for the wave and the greeting, 10 seconds for the press show. A press cancels anything running. Vehicles, animals and plain motion are ignored.

## Controls in Home Assistant

| Entity | Use |
|---|---|
| `input_boolean.halloween_mode` | turns the show on and off |
| `input_button.halloween_preview_approach`, `halloween_preview_ring` | run one show with the mode off; the bulbs return to where they were |
| `input_button.halloween_stop_restore` | stops everything and restores |
| `input_number.halloween_door_min` | front door minimum brightness, 120 |
| `input_boolean.halloween_approach_meow` | off; turning it on plays a quiet meow on a greeting, and the doorbell shows its stock talking picture while it plays |

## Status at arming

| Piece | State |
|---|---|
| Ring colors, pulse, spotlight | Seen working |
| Cat screens | Installed. In the preview the viewer reported "the normal one and one that is winking". The ringing screen during a real press was not seen |
| Ring sound | Installed and played on a real press. The viewer reported a large delay; the log shows about one second of file conversion on that first press |
| Screen watcher | Running; the screen stayed on |
| Bulbs | Snapshot taken with all four off, so midnight turns them off |
| Home Assistant package | 11 automations, 7 scripts, 32 entities |
| Temporary SSH key | Restricted to the commands in `doorbell/halloween.sh`; `restore` runs, `id` is refused |
| Not verified | A real driveway detection, a real doorbell person event, a press with the mode on, a full Stop & Restore, and the doorbell's own short timers expiring |

Idle lighting returns about 15 seconds after a press. The request said eight.

## Install

Replace `DOORBELL_IP` and `HOME_ASSISTANT_HOST` in the package as it is copied. Run the restore commands in the next section before turning the mode on.

The stock welcome sprite is named `efe2e540-435d-11b1-29a1-7d5a7391c654.png` in `display_off` and in the by-hand restore commands. That name exists on the author's doorbell. Take yours from `customAnimations` in your own backed-up `ubnt_lcm_gui.conf` and replace it in `doorbell/halloween.sh` and the commands below.

1. Copy the effect script and the ring sound to the doorbell's `/tmp`, and the two sprites and the sound to flash, each with a 32-character `.md5` file beside it (`md5sum FILE | cut -d' ' -f1 | tr -d '\n' > FILE.md5`): sprites in `/etc/persistent/lcm/animation/`, `halloween-ring.ogg` in `/etc/persistent/sounds/`.
2. On Home Assistant, create the key: `ssh-keygen -t ed25519 -N '' -C halloween-2026-temp -f /config/.ssh/halloween_ed25519`.
3. On the doorbell, add this line to `/etc/dropbear/authorized_keys` (not only the persistent file), with the public key from step 2:
   `command="sh /tmp/halloween.sh",no-port-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... halloween-2026-temp`
4. Install the package and restart Home Assistant once, because `shell_command` is a new domain there:
   `sed -e 's/DOORBELL_IP/192.0.2.10/' -e 's/HOME_ASSISTANT_HOST/homeassistant.local/' homeassistant/halloween_2026.yaml > /config/packages/halloween_2026.yaml`
5. Copy `sounds/meow-curious.mp3` to `/config/www/halloween/` on Home Assistant.

## Stop and restore

Press Stop & Restore or turn the mode off. Midnight does the same, then removes the SSH key and deletes the private key on Home Assistant. If Home Assistant restarts while armed, it runs the same restore after the bulbs come back.

### By hand, if Home Assistant is gone

From a machine that can log in to the doorbell (replace `DOORBELL_IP` with its address):

```sh
# ring back to stock, spotlight and green channel off
ssh ubnt@DOORBELL_IP '
echo 0 > /sys/class/leds/G/brightness; echo 0 > /sys/class/leds/torch1/brightness
ubnt_ipc_cli -T=ubnt_mcu_agent -r=1 -t=2000 -m="{\"functionName\":\"SetLEDStatus\",\"mode\":1,\"fgColor\":4,\"bgColor\":0,\"bright\":-1}"
# screen: original welcome, ringing override disabled, then dark
ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=4000 -m="{\"functionName\":\"ChangeLcmGuiSettings\",\"customAnimations\":[{\"count\":8,\"durationMs\":1600,\"enable\":false,\"file\":\"halloween-ringing.png\",\"guiId\":\"WAITING_FOR_RESPONSE\",\"loop\":true},{\"count\":1,\"durationMs\":100,\"enable\":true,\"file\":\"efe2e540-435d-11b1-29a1-7d5a7391c654.png\",\"guiId\":\"WELCOME\",\"loop\":true}]}"
ubnt_ipc_cli -T=ubnt_lcm_gui -r=0 -t=2000 -m="{\"functionName\":\"ShowGui\",\"brightness\":0}"
# ring sound: stock tone
ubnt_ipc_cli -T=ubnt_sounds_leds -r=0 -t=4000 -m="{\"functionName\":\"ChangeSoundLedSettings\",\"customSounds\":[{\"enable\":true,\"file\":\"Default.ogg\",\"repeatTimes\":1,\"soundStateName\":\"RING_BUTTON_PRESSED\",\"volume\":100}]}"
# temporary key
sed -i "/halloween-2026-temp/d" /etc/dropbear/authorized_keys /etc/persistent/.ssh/authorized_keys'
```

The same commands are in `doorbell/halloween.sh` under `stock`, `display_off` and `sound_off`, but a doorbell reboot deletes that script from `/tmp`.

On Home Assistant, delete `/config/.ssh/halloween_ed25519` and `/config/.ssh/halloween_ed25519.pub`, and remove `/config/packages/halloween_2026.yaml` and `/config/www/halloween/` when the season is over.

Before a season starts, save the doorbell's stock files and both `authorized_keys` files; [backups/README.md](backups/README.md) lists them and gives the command.

Do not send a full copy of the saved sound config to `ChangeSoundLedSettings`. The service rejects it and still returns `statusCode 0`.
