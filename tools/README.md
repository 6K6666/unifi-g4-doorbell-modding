# Tools

Small scripts for exploring and modifying the doorbell. Run them from the repository root on your own computer. Replace `DOORBELL_IP` with the doorbell's address.

| Tool | What it does | Changes the doorbell? |
|---|---|---|
| [copy-files.sh](copy-files.sh) | copies the doorbell's shell scripts and stock configs to a local folder, at low priority, so you can read and search them there | no |
| [extract-ipc-names.py](extract-ipc-names.py) | lists the message names found in copies of the doorbell's service programs | no (works on local files) |
| [install-ssh-key.sh](install-ssh-key.sh) | puts your public key where the doorbell's SSH server reads it; does nothing if it is already there | adds a line to `/etc/dropbear/authorized_keys` when the key is missing |
| [effect-template.sh](effect-template.sh) | a starting point for your own script: watchdog, one effect at a time, checked PID kills | only if you copy it to the doorbell and run it |
| [research/go-funcs.go](research/go-funcs.go), [research/go-string-method.py](research/go-string-method.py) | list the functions in a Go program such as the ring chip's `ubnt_mcu`, and print what a small enum `String()` method returns for each value | no (works on local files; needs Go and `llvm-objdump`) |

```sh
tools/copy-files.sh DOORBELL_IP doorbell-files            # then read and search doorbell-files/
tools/install-ssh-key.sh DOORBELL_IP                      # uses ~/.ssh/id_ed25519.pub
python3 tools/extract-ipc-names.py bin/ubnt_* > names.txt # after copying programs from /bin
```

Each tool was run against a real doorbell, except that the key installer's add path was not run; only its "already present" path was. The effect template was tested with a harmless effect that writes to a log: its watchdog fires after the starting session ends, a second start replaces the first, `stop` restores at once, and a stale PID is spared. See [running your own scripts](../docs/how-to/running-custom-scripts.md) for how to use it.
