# UniFi G4 Doorbell Pro: explore it, change it

The G4 Doorbell Pro has a color screen, a lit button ring, a spotlight, a speaker and a small computer inside. Ubiquiti's app only lets you change a few of those things. This repository shows how to get a shell on the doorbell, what is inside, and how to make it do things it does not do stock, with commands that have been run on a real unit and notes on what went wrong.

![The Halloween welcome screen on the doorbell's 240 by 240 display](examples/halloween-2026/assets/welcome.gif)

The picture above is the doorbell's own welcome screen, replaced with a custom animation. It comes from [the worked example](examples/halloween-2026/README.md): a one-night Halloween show that coordinated the doorbell, four lights and Home Assistant.

## What you can do with it

| You can | How hard | Details |
|---|---|---|
| Turn on SSH, which Ubiquiti leaves off | medium | [getting SSH access](docs/getting-started/getting-ssh-access.md) |
| Change the button ring's color, or make it pulse | easy | [quick start](docs/how-to/quick-start.md) |
| Turn the spotlight on and off from a script | easy | [quick start](docs/how-to/quick-start.md) |
| Show your own picture or animation on the screen | medium | [recipes](docs/how-to/recipes.md) |
| Play your own sound when someone presses the button | medium | [recipes](docs/how-to/recipes.md) |
| Keep the screen on instead of letting it go dark | medium | [recipes](docs/how-to/recipes.md) |
| Run your own scripts, started from Home Assistant or your computer | medium | [running your own scripts](docs/how-to/running-custom-scripts.md) |
| Read the light sensor and the doorbell's own log | easy | [recipes](docs/how-to/recipes.md) |

Not working yet: lighting single LEDs in the ring (it takes one color for the whole ring), playing a sound file from the shell, and anything that runs by itself after a reboot. [Verified controls](docs/reference/verified-controls.md) lists the details.

## Before you start

- This was learned on one doorbell: board G4R, system ID `0xa574`, firmware 5.5.45, behind a UniFi Protect NVR. Other firmware versions and the PoE model differ.
- You need to be comfortable pasting commands into a terminal. Every command has an undo next to it.
- Nothing here changes recording, notifications or the indoor chime. Changes that go wrong can still interrupt recording or need a recovery procedure. The [undo page](docs/how-to/undo-and-recovery.md) lists what to do.
- This project is not made by or affiliated with Ubiquiti. You use it at your own risk; the [license](LICENSE) says so.

## Where to start

| Your goal | Start here |
|---|---|
| I just want to try it | [getting SSH access](docs/getting-started/getting-ssh-access.md), then the [quick start](docs/how-to/quick-start.md) |
| I want to build something | [running your own scripts](docs/how-to/running-custom-scripts.md), [recipes](docs/how-to/recipes.md) and the [Halloween example](examples/halloween-2026/README.md) |
| I want to know how it works | the [documentation index](docs/README.md) and the [glossary](docs/glossary.md) |
| I use an AI coding assistant | point it at [AGENTS.md](AGENTS.md) first |

## What is in the repository

```
docs/
  getting-started/     SSH access, exploring without slowing the doorbell down
  how-to/              quick start, recipes, custom scripts, undo and recovery
  reference/           how the doorbell works: processes, flash, chips, messages, controls
  glossary.md
tools/                 small scripts: copy files off, install a key, bounded-effect template
examples/
  halloween-2026/      a full show built from all of the above
AGENTS.md              rules and facts for AI assistants
```

## How claims are labeled

Reference pages mark how each claim was checked: run (executed on a real doorbell), seen (a person watched or listened), logged (shown by the log), strings (read from the firmware, not tried) or stock script (read in Ubiquiti's own scripts, not run). A claim labeled only "strings" or "stock script" is a lead, not a result.

## Not in the repository

Ubiquiti's programs, sounds and images are not here, and neither are backups of anyone's doorbell. The scripts and docs use placeholders for addresses: `DOORBELL_IP`, `HOME_ASSISTANT_HOST` and `UDM_IP`.

## License

MIT, see [LICENSE](LICENSE). It covers the code, docs and the artwork and sounds in this repository.
