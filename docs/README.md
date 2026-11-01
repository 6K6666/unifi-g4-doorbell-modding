# Documentation

Pick the path that matches what you want to do. Each page says near the top what it covers and how risky it is.

## I want to try it

You have a G4 Doorbell Pro and some patience, and you are comfortable pasting commands into a terminal.

1. [Getting SSH access](getting-started/getting-ssh-access.md): switching on the shell that Ubiquiti leaves off
2. [Quick start](how-to/quick-start.md): change the ring color, light the spotlight, switch the screen, with an undo for each step
3. [Undo and recovery](how-to/undo-and-recovery.md): how to put anything back
   When you are done, [lock it back down](how-to/lock-it-back-down.md): turn SSH off or limit it to one address
4. [Recipes](how-to/recipes.md): custom welcome picture, custom ring tone, keeping the screen on

## I want to build something

You can read a shell script and edit a config file, and you want the doorbell to do something it does not do stock.

1. [Running your own scripts](how-to/running-custom-scripts.md): where scripts live, how to start them, how to make them clean up after themselves
2. [Recipes](how-to/recipes.md) and the [tools](../tools/README.md)
3. [The Halloween example](../examples/halloween-2026/README.md): a complete show that coordinates the doorbell, four lights and Home Assistant, with a [write-up of what went wrong along the way](../examples/halloween-2026/docs/build-and-review.md)

## I want to understand how it works

You like knowing why. These pages describe the doorbell itself; they change nothing.

| Page | What it tells you |
|---|---|
| [System map](reference/system-map.md) | the processor, memory, flash layout, boot sequence and the programs that run |
| [Filesystem and persistence](reference/filesystem-and-persistence.md) | what can be written, what survives a restart, what overwrites your changes |
| [Hardware map](reference/hardware-map.md) | the chips inside and how to reach each one |
| [IPC and services](reference/ipc-and-services.md) | the internal messages and how to send them |
| [LED, sound and screen control](reference/led-sound-and-screen-control.md) | the ring, screen and sound options the firmware offers |
| [Which model has what](reference/models.md) | how the non-Pro, Pro, PoE and G6 Entry differ, and whether the recipes apply |
| [Verified controls](reference/verified-controls.md) | what has been shown to work on a real doorbell, with the details |
| [Message, state and screen names](reference/data/) | raw lists taken from the firmware |
| [Exploring safely](getting-started/exploring-safely.md) | how to look around without slowing the doorbell down |

## Words you might not know

[Glossary](glossary.md).

## Using an AI assistant

The repository root has an [AGENTS.md](../AGENTS.md) written for AI coding assistants. Point your assistant at it before you let it near the doorbell.

## How to read the evidence labels

Claims in the reference pages carry a label:

| Label | Meaning |
|---|---|
| run | a command was executed on a real doorbell and the result observed |
| seen | a person watched or listened and reported |
| logged | the doorbell's log or a readback showed it |
| strings | read out of the firmware's programs, not tried |
| stock script | read in the firmware's own scripts, not run here |

Anything labeled only "strings" or "stock script" is a lead, not a result.
