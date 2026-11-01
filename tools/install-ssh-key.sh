#!/bin/sh
# Put your public key where the doorbell's Dropbear reads it (/etc/dropbear/authorized_keys). Safe to run twice.
# Usage: tools/install-ssh-key.sh DOORBELL_IP [PUBKEY_FILE]     (default key: ~/.ssh/id_ed25519.pub)
# ssh-copy-id writes to /etc/persistent/.ssh/authorized_keys, which the doorbell ignores. The Dropbear file may
# not survive a reboot (untested), so run this again if key login stops working.
set -eu
host=${1:?usage: install-ssh-key.sh DOORBELL_IP [PUBKEY_FILE]}
key=$(cat "${2:-$HOME/.ssh/id_ed25519.pub}")
case "$key" in *"'"*) echo "key contains a quote; refusing" >&2; exit 1;; esac
ssh "ubnt@$host" "f=/etc/dropbear/authorized_keys; grep -qxF '$key' \$f 2>/dev/null && echo 'key already present' || { printf '\n%s\n' '$key' >> \$f && echo 'key added'; }; chmod 600 \$f"
