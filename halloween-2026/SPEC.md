# Haunted Witch Cat: Halloween Tonight

The request as given on 2026-10-31.

## Experience

Use your uploaded witch-cat concept for the display, coordinated with the three driveway LIFX lights, Front Door Light, doorbell ring, and bottom spotlight.

Manually activate after testing. Automatically stop and restore normal settings at **midnight, November 1, 2026, America/Denver**. No annual recurrence.

| Trigger | Lighting sequence | Display and sound |
|---|---|---|
| Armed, idle | Driveway lights alternate dim purple and orange. Front Door Light stays warm amber. Doorbell ring slowly breathes amber if supported. | Witch cat blinks occasionally; pumpkins flicker and leaves drift. No ambient sound. |
| Driveway camera detects a person | A four-second orange wave runs through Driveway Lights 1-3, ending at the front-door fixture. | Silent buildup. |
| Doorbell detects a person | Ring brightens purple-to-orange. Bottom spotlight performs one gentle candle flicker, then provides steady illumination. | One quiet, curious meow. Welcome cat remains visible. |
| Doorbell pressed | Two soft red heartbeat pulses followed by an orange/purple flourish. Front-door illumination stays above its tested walking-light minimum. | Cat widens its eyes and reacts; a short magical meow ends with a tiny cackle. Matching cat animation replaces the generic "Ringing" screen. |
| Eight seconds after press | Return to Halloween idle lighting. | Sound finishes; cat remains in the appropriate welcome or waiting state. |

Use smooth fades, with no rapid strobing or full-path blackout.

## Controls and coordination

- Add a Home Assistant **Halloween Mode** toggle, **Preview Approach**, **Preview Ring**, and **Stop & Restore** controls.
- Use `event.front_yard_driveway_smart_detection`, filtered to person detections, for the driveway buildup.
- Use `binary_sensor.g4_doorbell_pro_person_detected` for the near-door greeting and `event.g4_doorbell_pro_doorbell` for button presses. Verify their actual event behavior during testing.
- Control `light.driveway_light_1` through `_3` and `light.front_door_light` individually. Confirm physical order during the preview.
- Give ringing priority over approach effects. Cancel the approach sequence when pressed; never overlap audio or queue shows. Apply a 45-second approach cooldown and ten-second ring-show cooldown. Normal doorbell notifications and indoor chime continue on every press.
- Ignore unavailable/unknown transitions and historical events loaded during startup. Passing vehicles, animals, and generic motion do not start the show.
- Leave existing lighting, speech, lock, and NFC automations in their present states.

## Doorbell artwork, lights, and audio

- Preserve the original welcome image and configurations before changes.
- Produce two compact 240 x 240 animations from the uploaded concept: a gentle welcome loop and a more expressive ringing loop. Preserve the cat, hat, pumpkins, and legible text.
- Override both `WELCOME` and `WAITING_FOR_RESPONSE`; preserve other display states, including active conversation and system warnings.
- Use Home Assistant's existing doorbell speaker integration for the approach cue. Use a device-local visitor-tone asset for the button sound, preventing duplicate outdoor playback. Keep the mechanical indoor chime unchanged.
- Start auditions quietly: approximately 20% approach volume and 35% ring volume, then calibrate outdoors with you.
- Run smooth doorbell LED effects locally rather than sending SSH commands for every animation frame. Home Assistant sends only fixed start/stop commands through verified SSH access.
- First map the physical LEDs with you watching. The channel names do **not** yet establish which controls operate the ring, display backlight, or bottom spotlight. Only proven controls enter the show; unsupported effects remain disabled.
- Preserve stock service behavior, recording, IR illumination, and two-way audio. Avoid firmware changes or a new MQTT service.

## Recovery and tonight-only operation

- Save original light states, effects, brightness, colors, display configuration, and modified audio settings before activation.
- Turning the mode off cancels running effects and restores that snapshot. Midnight performs the same shutdown.
- Add date/expiry checks to prevent reactivation after tonight. On Home Assistant restart, recover conservatively to off and restore saved settings rather than resuming a show.
- Doorbell effects have bounded execution and cleanup; loss of the controller must not leave a pulsing worker running indefinitely.
- Keep backups available if a device is unreachable during restoration, and report incomplete restoration explicitly.

## Validation and activation

1. Back up and verify restoration inputs before installation.
2. With you watching, identify LEDs at low brightness, confirm driveway light order, and establish a usable minimum doorstep brightness.
3. Preview both animations locally and verify the physical welcome-to-ringing transition.
4. Audition both sounds outside; verify no doubled stock visitor tone and no interference with conversation audio.
5. Walk the driveway-to-door route, press the button, and test repeated detections and presses.
6. Verify recording, notifications, indoor chime, Stop & Restore, and the midnight shutdown logic.
7. Activate immediately after these checks pass.

No hardware effects or new sounds have been tested yet. Physical LED mapping and firmware override behavior remain the main implementation risks.

## Decisions made during the build

- The ring cannot show purple. Pink stands in for purple and red plus a little green gives orange. Amber breathing is not supported, so the ring idle effect is disabled.
- Take over the bulbs: the show replaces the custom LIFX app effect on Driveway Lights 1-3 and the Front Door Light while Halloween Mode is on.
