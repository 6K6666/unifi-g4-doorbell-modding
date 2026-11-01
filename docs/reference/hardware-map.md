# Hardware map

In short: a list of the chips inside the doorbell, the wires they hang off, and the files that read or set them. Useful when you want to know whether a feature exists in hardware before you hunt for the software.

The chips on the doorbell, the bus each one sits on, and the Linux interface that reaches it. Taken from `/sys`, `/proc` and the loaded kernel modules on a G4 Doorbell Pro (system ID 0xa574). Labels are explained in the [system map](system-map.md). Reads only: nothing on this page was written to except the LED and torch channels described in the [control reference](verified-controls.md).

## Chips by bus

| Bus and address | Chip | Linux interface | Role |
|---|---|---|---|
| I2C 0, 0x01 | OmniVision OS05A10 | `os05a10` module, `/dev/iav` pipeline | main 5 MP camera sensor |
| I2C 0, 0x02 | OmniVision OV8856 | `ov8856_mipi` module | second sensor, the package camera |
| I2C 2, 0x28 | NXP PN547 | `/dev/pn544`, `pn5xx_i2c` module | NFC reader |
| I2C 2, 0x29 | ST VL53L1 | `/dev/stmvl53l1_ranging`, an input device named "STM VL53L1 proximity sensor" | time-of-flight distance sensor, feeds person-in-front |
| I2C 2, 0x30 | TI LP5562 | `/sys/class/leds/{R,G,B,W}` | four-channel LED driver; only `G` showed a visible effect |
| I2C 2, 0x44 | TI OPT3001 | IIO device `iio:device0` | ambient light sensor |
| I2C 2, 0x48 | NCT75 | sensor on the bus; no hwmon name exposed | board temperature |
| I2C 2, 0x63 | TI LM3644 | `/sys/class/leds/{torch,torch1,torch2,flash,flash1,flash2,indicator}` | dual-channel torch and flash LED driver; the spotlight |
| SPI 0.0 | `m25p80` | MTD | SPI NOR flash |
| SPI 0.1 | Sitronix ST7789V2 | `fb_st7789v2`, framebuffer `fb2`, 240 by 240, 16 bits per pixel | the LCD |
| SPI 1.0 | Cirrus Logic CS47L35 | `snd_soc_cs47l35`, ALSA card 0 | audio codec (Madera family) |
| SPI 1.1 | `spidev` (device tree `ambarella,spidev`) | `/dev/spidev1.1` | raw userspace SPI; the attached chip is unidentified |

The button ring is not on this list. It is driven by a separate microcontroller reached through `ubnt_mcu`; no I2C or SPI address was identified for it.

## Other interfaces

| Interface | Detail |
|---|---|
| PWM | one controller, `pwmchip0`, four channels. The LCD backlight uses it (`pwm_bl`, brightness 50 of 99 at the survey). A stock script, `buzzer_sounds.sh`, drives a buzzer through `/sys/class/pwm/pwmchip9/pwm0`, a path that does not exist on this unit |
| Backlight | two entries under `/sys/class/backlight`: `pwm_bl` and `fb_st7789v2` (brightness 10 of 15) |
| Framebuffers | `fb0` and `fb1` at 720 by 960 (the video overlay), `fb2` at 240 by 240 (the LCD) |
| GPIO | one chip, `ambarella-gpio`, 160 lines; line 69 is exported as an input reading 0 |
| Audio | ALSA card 0 (the codec, with DSP mixer controls) and card 1 (a loopback); a software volume control named `UBNT_SVOLUME` |
| Network | `wlan0` on a Broadcom `bcmdhd` driver; Bluetooth through `hci_uart` and `btbcm`; the `wl` tool is installed |
| USB | device-mode gadget modules (`usb_f_rndis`, `usb_f_ecm`) and USB Ethernet host drivers (`r8152`, `ax88179_178a`) are loaded; no physical USB port was identified |
| Clock | `rtc0` exists although the board features list no RTC |

Kernel modules loaded: the Bluetooth and Wi-Fi stack, the two LED drivers, `ubnt_gpio`, `ubnt_lock`, the camera sensors, the Ambarella video pipeline (`iav`, `dsp`, `imgproc`), the audio stack, `hts221` (a humidity sensor driver with no matching device on the bus), `spidev`, `cryptodev`.

## Reading the sensors

Safe reads that need no tools beyond the shell:

```sh
cat /sys/bus/iio/devices/iio:device0/in_illuminance_input   # lux; 0.18 at the survey
cat /sys/class/backlight/*/brightness
cat /sys/class/gpio/gpio69/value
```

Factory tools in `/usr/local/bin` read and write the buses directly: `i2c_access0`, `i2c_access1`, `i2c_access2` (I2C), `vl53l1_reg` (distance sensor registers), `amba_debug`, `phio`. They have no safeguards. Writing to a driver chip's registers can leave the ring, spotlight or screen in a state only a reboot clears.

## Open items

- Which chip the raw SPI device at `spidev1.1` is.
- Whether the LCD can be drawn to directly through `/dev/fb` while `ubnt_lcm_gui` is running. It was not tried.
- What the `torch2` and `flash` channels of the LM3644 drive. The infrared illuminators are the likely candidates and cannot be judged by eye.
- Which hardware the microcontroller connects the ring to, and whether the ring has more than one LED zone.
