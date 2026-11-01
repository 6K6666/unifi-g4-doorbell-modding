# Backups before a season

Save these before changing anything on the doorbell. They are the inputs for restoring it. The files stay on your machine: this folder's contents are gitignored, because they include Ubiquiti's own sounds and images and your SSH key lines.

On the doorbell:

- `/etc/persistent/ubnt_lcm_gui.conf` (screen animations)
- `/etc/persistent/ubnt_sounds_leds.conf` and `/etc/ubnt_sounds_leds.conf` (ring sound and lights)
- `/etc/persistent/lcm/` (sprites and their `.md5` files)
- `/etc/persistent/sounds/` (ring tones and their `.md5` files)
- `/usr/etc/gui/` (stock screen definitions for your board)
- `/etc/dropbear/authorized_keys` and `/etc/persistent/.ssh/authorized_keys`

```sh
ssh ubnt@DOORBELL_IP 'tar czf - -C / etc/persistent/ubnt_lcm_gui.conf etc/persistent/ubnt_sounds_leds.conf etc/ubnt_sounds_leds.conf etc/persistent/lcm etc/persistent/sounds usr/etc/gui' > doorbell-original.tgz
ssh ubnt@DOORBELL_IP 'cat /etc/dropbear/authorized_keys' > authorized_keys.dropbear.orig
ssh ubnt@DOORBELL_IP 'cat /etc/persistent/.ssh/authorized_keys' > authorized_keys.persistent.orig
```

Do not archive all of `/etc/persistent`. It holds the doorbell's SSH host key and its controller certificates.
