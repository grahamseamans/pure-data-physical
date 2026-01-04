# Pure Data Physical

A protocol for networked audio hardware. Any device that speaks this protocol can join a Pure Data patch over the network.

## What is this?

Your computer runs Pure Data with a "brain" patch. Physical hardware modules connect over Ethernet. When a module connects, it sends its Pd subpatch to the brain, which instantiates it into the running patch.

Modules have >1 conductor connections for patching (gnd + signal). When you connect a cable between two modules, they perform a peer-to-peer handshake to discover each other, then inform the brain of the connection. The brain updates the Pd patch graph accordingly.

**Audio does not flow through the cables.** Cables signal topology only of course. All audio lives in Pure Data.

- **Total recall**: Modules use endless encoders with RGB LEDs. No knob positions to remember. Save and load entire sessions - connections, parameters, everything.
- **Self-describing**: Each module carries its own Pd patch. Plug it in, it exists in software.
- **Scale agnostic**: Make each part as "small" as you want. your atoms could be oscialltors and envelopes or drum machines and polysynths. 

## Core Concepts

### The Brain

A Pure Data patch running on a computer. Listens for module announcements, instantiates subpatches, manages connections, sends data to controllers for display, handles recording/playback.

### Modules

Physical hardware that:
- Connects to the brain over Ethernet (plan: PoE for power + data)
- Sends its Pd subpatch on connection
- Has TS jacks for patching to other modules
- Sends parameter changes (encoder turns, button presses) to the brain
- Receives state from the brain

### Connections (Cables)

TS cables between module jacks. When a cable is inserted:
- Wait briefly, listen for a hello message through the cable
- If hello (id + jack) received: tell brain who you're connected to
- if no hello recieved, send hello

(Exact protocol TBD)

## Message Types

### Module → Brain

- **hello**: Module announcing itself, includes module ID and embedded Pd patch
- **goodbye**: Module disconnecting
- **param**: Parameter change (encoder turned, button pressed)
- **connect**: "My jack X is now connected to module Y jack Z"
- **disconnect**: "My jack X is no longer connected"

### Brain → Module

- some sort of state change about somethign that the module mirrors
- **state**: Full state dump (for recall)

### Module ↔ Module (through cable)

- **handshake**: Identity exchange when cable connects

(Exact message format TBD - likely OSC)

## Status

Just starting. Currently prototyping the brain patch in Pure Data using OSC loopback to simulate modules.

## Hardware Plans

- ESP32-based modules (WiFi/Ethernet + PoE)
- Endless encoders with RGB LED rings
- TS jacks with connection detection

## License

Some sort of open source
probably same liscence as pd
tbd
