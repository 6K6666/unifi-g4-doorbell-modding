# Which model has what

In short: every recipe in this repository was run on one G4 Doorbell Pro (system ID `0xa574`). The non-Pro (`0xa571`) and PoE (`0xa575`) have their own files in the same firmware, so the commands exist on them, but only the Pro's hardware was checked.

Firmware 5.5.45 contains settings for several doorbells. This page compares what that firmware's own files say about each. Nothing here was run on the other models, so every cell is labeled "stock files" (read from the copied firmware files) unless it says run.

Find your model's ID with `grep sysid /etc/board.info` on the doorbell.

## Comparison

| | G4 Doorbell (non-Pro) | G4 Doorbell Pro | G4 Doorbell Pro PoE | G6 Entry |
|---|---|---|---|---|
| System ID | `0xa571` | `0xa574` | `0xa575` | `0xa063`, `0xa064` |
| Tested here | no | yes (run, seen) | no | no |
| Screen | monochrome, 28 screens (stock files) | color, 49 screens (stock files) | same table as the Pro (a symlink, stock files) | no table in this firmware |
| Screen backlight | `fb_sp8110` | LP5562 channels `B` and `W` | as the Pro | unknown |
| Own feature file | yes; no color screen, no package camera | yes | yes | none |
| Stock sounds | 6 files | 8 files (adds `denied.ogg`, `success.ogg`) | 8 files | none |
| Default sound and LED settings | same as the Pro | same | same | none |
| Per-LED control (stock script) | no | no | yes: `testLed.sh` names LEDs A1 to A4 and B1 (RGB) and C1, C2 (white) on a KTD2061 driver | yes, same script |

## Do the recipes apply?

| Recipe | Non-Pro | Pro PoE | G6 Entry |
|---|---|---|---|
| SSH access | likely: same Protect setting | likely | unknown |
| Ring color and pulse | likely; commands are shared, the ring was not checked | likely, but its LEDs sit on a different driver, so colors may differ | unknown |
| Spotlight (torch driver) | unknown; the Pro's torch driver is an LM3644 at I2C 2-0063 | unknown | unknown |
| Custom screen picture | no: its screen is monochrome, so a color picture will not fit | likely, same screen table | unknown |
| Custom ring tone | likely, same sound service | likely | unknown |
| Read the light sensor and log | likely | likely | unknown |

"Likely" means the stock files match the Pro's. It does not mean someone tried it.

## Other findings from the stock files

- Feature file `0xa576` is identical to the Pro's, and no model name for it was found.
- ID `0xa597` appears as `UBNT_SYSID_UVC_DUT_4`, an internal test board with 31 screens and an LP5012 backlight. It is not a product.
- The G6 Doorbell Lite (`0xa061`, `0xa062`) and G6 Entry Pro (`0xa06d`) also appear only as constants and in the shared LED script.

## If you have a different model

1. Run [tools/copy-files.sh](../../tools/copy-files.sh) and compare your files with the Pro's, as in the [AGENTS.md](../../AGENTS.md) firmware steps.
2. Start with the read-only commands in the [quick start](../how-to/quick-start.md), step 2.
3. Try one change at a time with someone watching, and report what you saw.
