# Glossary

Plain-language meanings for the terms used in these docs. Skip what you already know.

| Term | What it means here |
|---|---|
| Firmware | the software built into the doorbell. This repository was written against version 5.5.45 |
| Protect, NVR | UniFi Protect is Ubiquiti's camera software. The NVR is the box that runs it and records video, often a UDM Pro or a Cloud Key. The doorbell reports to it |
| UDM | the UniFi Dream Machine router that hosts Protect for many homes |
| SSH | a way to type commands on another computer over the network. The doorbell has it switched off until you turn it on |
| Shell | the command prompt you get after logging in over SSH. On the doorbell it is BusyBox `sh`, a small shell with fewer features than the one on your laptop |
| Recovery code | a code shown in Protect for the doorbell. It works as the SSH password for the `ubnt` account |
| Dropbear | the small SSH server on the doorbell. It reads allowed keys from `/etc/dropbear/authorized_keys` |
| Forced command | an SSH key setting that makes the key run one fixed command and nothing else |
| Sysid, board | the doorbell's model code. This repository's findings are for sysid `0xa574` (G4 Doorbell Pro) |
| Flash, persistent volume | the doorbell's saved storage. Files in `/etc/persistent` stay when the power goes out |
| Read-only | a filesystem you cannot write to. The doorbell's main system files are read-only, which protects them from mistakes |
| tmpfs, memory disk | folders such as `/tmp` that live in memory and empty themselves on restart |
| Reboot | restarting the doorbell. It clears `/tmp` and anything running there |
| Service | a program that runs all the time, for example the one that handles the screen. They talk to each other with messages |
| IPC | inter-process communication: the doorbell's internal message system. `ubnt_ipc_cli` sends one message from the shell |
| statusCode 0 | the message was delivered. It does not mean the change worked; check the log and look at the device |
| Log, `logread` | the doorbell's record of what its services did. `logread \| tail` shows the latest lines |
| sysfs | files under `/sys` that read and set hardware, such as `echo 10 > /sys/class/leds/torch1/brightness` |
| I2C, SPI | two ways the doorbell's main chip talks to small chips such as the light driver, the sensors and the screen |
| MCU | a small separate microcontroller chip. One of them runs the button ring |
| LED driver | a chip that controls LED brightness. The doorbell has two you can reach |
| PWM | a way of dimming a light or setting a tone by switching it on and off fast |
| Watchdog | a timer that puts things back if nothing else does. Every effect in these docs has one |
| PID | the number of a running program, used to stop it. Numbers get reused, so check before you stop one |
| Home Assistant | free home-automation software. This repository uses it to start effects from camera and doorbell events |
| `strings` | a tool that lists the readable text inside a program file. Used here to find the names of messages and settings |
| Evidence labels | run, seen, logged, strings, stock script. They say how a claim was checked; see the [README](../README.md) |
