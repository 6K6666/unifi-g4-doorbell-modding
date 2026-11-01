# Getting SSH access to the doorbell

Risk: medium. It switches on SSH for every camera Protect manages and restarts Protect, which pauses recording on all cameras for a few minutes.

A G4 Doorbell Pro ships with SSH switched off, and Protect has no setting to turn it on. Getting a shell took four separate fixes: the UDM's own SSH, a Protect config override, the override file's ownership, and the key file Dropbear reads. This page lists them in the order they are needed.

The steps come from the log of the session that first got in: a UDM Pro running UniFi OS 5.1.34 with Protect 7.3.74, and a doorbell on firmware 5.5.45. Step 6 is copied from that log. Step 3 combines the log's first command with the ownership fix it needed later, and was not run as written. Step 7 was tested while writing this page. The list at the end names what was never tested.

## What the failure looks like

`ssh ubnt@DOORBELL_IP` prints `Connection refused`. Nothing listens on port 22. The same refusal from a shell on the UDM shows that routing and VLANs are fine.

## Settings that do not enable SSH

- The "Device SSH Authentication" setting in UniFi Network. Ubiquiti documents it for network devices. It has no effect on a Protect camera, and the doorbell kept refusing.
- The Protect API tools available to the session. They could change IR mode, HDR, volume, name and motion detection. None of them could touch SSH.
- The manual recovery code under the doorbell's Protect settings. It is the SSH password for the `ubnt` account (a password prompt accepted it once port 22 was open), but it does nothing while the port is closed.

## Steps

1. Get a shell on the UDM. Console SSH is off by default too. Ubiquiti's documentation puts the switch under Control Plane, then Console, in the UDM's settings; turn SSH on and set a password. Then install your key so later steps do not need the password:

   ```sh
   ssh-copy-id -i "$HOME/.ssh/id_ed25519.pub" root@UDM_IP
   ```

2. Confirm the default. On the UDM:

   ```sh
   grep -n '"enableSsh"' /usr/share/unifi-protect/app/config/default.json
   ```

   It prints `"enableSsh": false`.

3. Override it for Protect. The session took this method from the setup section of the kapowaz/doorbell-tool project; that page was not checked for this guide. On the UDM:

   ```sh
   config=/etc/unifi-protect/config.json
   [ -f "$config" ] && cp -p "$config" "$config.backup-$(date +%Y%m%d-%H%M%S)"
   if [ -f "$config" ]; then jq '.enableSsh = true' "$config" > "$config.new"
   else printf '{"enableSsh":true}\n' > "$config.new"; fi
   chown unifi-protect:unifi-streaming "$config.new"
   chmod 600 "$config.new"
   mv "$config.new" "$config"
   runuser -u unifi-protect -- jq -e '.enableSsh == true' "$config"
   systemctl restart unifi-protect
   ```

   The `chown` line is the one the first attempt missed (see the next section). According to that source the override applies to every camera Protect manages; only the doorbell was checked. The restart interrupts recording on all cameras.

4. Check that port 22 is open, from the UDM and from your own machine:

   ```sh
   nc -vz DOORBELL_IP 22
   ```

5. Log in with the recovery code. User `ubnt`, password is the recovery code. OpenSSH shows the doorbell's ECDSA host key fingerprint on the first connection; note it.

   ```sh
   ssh ubnt@DOORBELL_IP
   ```

6. Install your key where Dropbear reads it. `ssh-copy-id` writes to `/etc/persistent/.ssh/authorized_keys`, and the doorbell ignores that file. Run `ssh-copy-id` once anyway, then, in the doorbell's shell, copy the line across:

   ```sh
   while IFS= read -r key; do
     [ -z "$key" ] && continue
     grep -qxF "$key" /etc/dropbear/authorized_keys ||
       printf '\n%s\n' "$key" >> /etc/dropbear/authorized_keys
   done < /etc/persistent/.ssh/authorized_keys
   chmod 600 /etc/dropbear/authorized_keys
   ```

   No restart is needed. A key login from your machine should now work without a password.

7. Copy files with `scp -O`. The doorbell has no SFTP server. Plain `scp` of a small file to `/tmp` failed with `sh: /usr/libexec/sftp-server: not found` and `scp: Connection closed`; with `-O` the same copy worked.

## Problems found during setup

- The override file had the wrong owner. The first version was written by root with mode 600. Protect runs as `unifi-protect`, so it could not read the file, logged that, and carried on with SSH off. Port 22 stayed closed until the owner was changed and Protect restarted.
- `ssh-copy-id` reported success twice and the key still failed. It added the line to the persistent file. `/etc/dropbear/authorized_keys` was empty (0 bytes, timestamp December 1999) and is the file Dropbear reads. Checking `ls -l` on both files in the doorbell's shell is what exposed it.
- Newer OpenSSH clients are dropped during key exchange. Add `-o HostKeyAlgorithms=ecdsa-sha2-nistp256`. The [control reference](../reference/verified-controls.md) has the detail.
- The Protect restart looked worse than it was. Right after it, the API listed all five cameras as disconnected, while the doorbell's recording files were being written again. Only the doorbell's recording was checked.

## Undo

Delete `/etc/unifi-protect/config.json` if the override created it, or copy the `.backup-` file back over it, and restart Protect. Remove your key lines from `/etc/dropbear/authorized_keys` and `/etc/persistent/.ssh/authorized_keys`. Turn console SSH off again on the UDM if you no longer need it. None of this was run.

## Not tested

- Whether the key in `/etc/dropbear/authorized_keys` survives a doorbell reboot.
- Whether the Protect override survives a Protect or UniFi OS update.
- Whether other cameras open port 22 after the override. Only the doorbell was checked.
