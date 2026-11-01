#!/bin/sh
# Copy the doorbell's shell scripts and stock configs to this machine, at low priority, so they can be read and searched here.
# Usage: tools/copy-files.sh DOORBELL_IP [OUTDIR]     (default OUTDIR: ./doorbell-files)
# Leaves out /etc/persistent, passwd, Wi-Fi settings, certificates and keys, and the stock account config files.
# The doorbell has little spare CPU: do not replace this with a recursive grep on the device.
set -eu
host=${1:?usage: copy-files.sh DOORBELL_IP [OUTDIR]}
out=${2:-doorbell-files}
mkdir -p "$out"
ssh "ubnt@$host" 'cd / && nice -n 19 tar cf - linuxrc usr/local/bin/*.sh usr/local/bin/*.cfg usr/local/bin/scripts usr/etc/rc.d usr/etc/init.d usr/etc/conf usr/etc/gui/*.json usr/etc/features*.json usr/etc/sysconfig usr/etc/lighttpd usr/etc/cronjobs usr/etc/hotplug.d usr/etc/hotplug2.rules usr/etc/banner bin/*.sh usr/bin/*.sh usr/lib/*.sh 2>/dev/null' | tar xf - -C "$out"
echo "copied $(find "$out" -type f | wc -l | tr -d ' ') files to $out"
