# Haunted Witch Cat Implementation Plan

Goal: Tonight-only doorbell and LIFX show, restoring at 2026-11-01 00:00 America/Denver.
Architecture: One Home Assistant package owns triggers, cooldowns, UI controls, snapshots and restoration. Stock doorbell display/sound overrides and a bounded local LED worker provide device effects through fixed SSH commands.
Spec: User-approved Haunted Witch Cat plan in this chat.
Constraints: No firmware change, MQTT service, lock/NFC change, IR change, or overlapping audio. Only physically mapped LEDs. Preserve mechanical chime and recording.

- [ ] Back up doorbell display/sound configuration and assets, HA light states and relevant configuration. Confirm restoration inputs are readable.
- [ ] Map ring and spotlight via stock controls with owner watching; unsupported controls stay disabled. Confirm sound volume and physical driveway order.
- [ ] Build two 240px sprite animations and short meow assets; validate dimensions, count, duration, size, loop and decode. Preserve original assets.
- [ ] Test trigger filtering, expiry, cooldown, priority and restoration before writing package and bounded doorbell worker.
- [ ] Install inert package and assets, validate HA config, reload only required domains (restart only if necessary). Add card and helpers.
- [ ] Attended previews; validate cat during ringing, lights, sounds, recording/chime, restart recovery and restore. Activate only after checks pass.

Review focus: repeated detections; stale startup event; ring preempts greeting; network failure during restore; midnight during active show.
