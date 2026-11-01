# Lock it back down

Risk: medium. Turning SSH off restarts Protect, which pauses recording on every camera for a few minutes. Nothing on this page was run on a real system; each step says what it is based on.

SSH on a doorbell is a root shell on a device that sees your front door. The recovery code is its password, and anyone who has it and can reach port 22 can drive the ring, the speaker and the screen, read the doorbell's files and stop it recording. This page covers three ways to shrink that: turn SSH off, allow it from one address only, or keep it on and make sure it never faces the internet.

## What SSH exposes

- Port 22 on the doorbell, answered by Dropbear, with the recovery code as the `ubnt` password until you add a key.
- The Protect override described in [getting SSH access](../getting-started/getting-ssh-access.md) sets `enableSsh` for every camera Protect manages, not only the doorbell. Other cameras on the same NVR may now answer on port 22 as well. Check with `nc -vz CAMERA_IP 22` from your own machine.
- The recovery code is shared by the doorbell's Protect page. Treat it as a password: do not paste it into chat or commit it.

## Option 1: turn SSH off

Based on reversing the steps in the setup page; not tested.

1. On the UDM, set the override back. Either delete the file you created, or restore the backup the setup step made (`config.json.backup-DATE` in `/etc/unifi-protect/`):

   ```sh
   config=/etc/unifi-protect/config.json
   ls "$config".backup-*          # a backup exists only if a config file was there before
   rm "$config"                   # or: mv "$config".backup-DATE "$config"
   systemctl restart unifi-protect
   ```

   If the file held other settings before you started, restore the backup instead of deleting it.
2. Wait for the doorbell to reconnect, then from your computer:

   ```sh
   nc -vz DOORBELL_IP 22
   ```

   "Connection refused" means it worked. Whether the doorbell closes a port that is already open without a restart was not tested; if it stays open, restart the doorbell from Protect.
3. Remove what you added while it was on: your key lines in `/etc/dropbear/authorized_keys` (they live in memory and may already be gone after a restart), and any scripts in `/etc/persistent`. [Undo and recovery](undo-and-recovery.md) lists the rest.

## Option 2: allow SSH from one address

Keep SSH on for yourself, and let only one machine reach it. Do this in the firewall that sits between your networks, not on the doorbell, which has no firewall tool that was checked here.

1. Give the machine that needs access (your computer, or Home Assistant) a fixed address in your router's DHCP settings.
2. Add a firewall rule, with the doorbell as the destination and TCP port 22: allow from that one address, block from everything else. Put the allow rule above the block rule. In UniFi Network these live under Security, in the firewall or policy settings; the menu names change between versions.
A firewall only sees traffic that crosses the router. If the doorbell shares a network or VLAN with the machines you want to block, they reach port 22 directly and the rule does nothing, so this works only when the doorbell is on its own network.
3. Test from a different machine. `nc -vz DOORBELL_IP 22` should time out or be refused. Test again from the allowed one; it should connect.

If a Home Assistant machine runs your effects, a [forced-command key](running-custom-scripts.md#starting-a-script-from-outside) limits what that one machine can do even when it is allowed in.

## Option 3: never forward it to the internet

- Do not create a port forward from your router to the doorbell's port 22, and do not put the doorbell in a DMZ.
- Reach it from outside through a VPN into your network, not by opening a port.
- Check from outside your home network. From a phone on mobile data with Wi-Fi off, a port scanner app pointed at your public address should show port 22 closed. Your public address is shown by your router's status page.
- Look at your router's port-forward list now. Anything pointing at the doorbell or the NVR's camera network that you did not mean to leave is worth removing.

## Which to choose

| Situation | Use |
|---|---|
| You are done experimenting | Option 1 |
| You run scripts from Home Assistant | Option 2, plus Option 3 |
| You use SSH occasionally | Option 1 until you need it; turning it on again takes the setup steps and a Protect restart |

## Not tested

- Whether removing the override closes port 22 without restarting the doorbell.
- Whether the Dropbear key file survives a reboot.
- The firewall steps; they follow how UniFi rules usually work and were not run on this network.
