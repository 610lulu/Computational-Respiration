# Computational Respiration

A stable ESP32 light prototype that turns a continuous thermal-load signal into colour, brightness and breathing rhythm.

The prototype has one input, `heatValue` (0–100). A low value is a dim warm white with a slow breath; a high value is a brighter orange-red with a faster, more visible breath. The firmware smooths both the load and the breathing phase, so a new value never causes a visible jump.

## Hardware baseline

This repository targets the following purchase configuration:

- ESP32 DevKit V1 / ESP32-WROOM-32
- 4-pin RGB LED module with an onboard resistor network, **common cathode**
- USB cable and breadboard jumper wires
- If using a bare RGB LED, add one resistor (220–330 Ω) in series with each R/G/B channel.

Suggested wiring for the baseline module:

| RGB module | ESP32 DevKit |
| --- | --- |
| R | GPIO 25 |
| G | GPIO 26 |
| B | GPIO 27 |
| common cathode / GND | GND |

![ESP32 RGB wiring diagram](docs/wiring-diagram.svg)

For a common-anode module, set `COMMON_ANODE` to `true` in `firmware/ComputationalRespiration.ino` and connect the common pin to 3V3. Do not connect an unknown module until its pinout and resistor arrangement are confirmed.

The full purchase and bench checklist is in [docs/hardware-checklist.md](docs/hardware-checklist.md).

## Upload and run

1. Install Arduino IDE and the Espressif **esp32** board package.
2. Select **ESP32 Dev Module** and the correct serial port.
3. Open `firmware/ComputationalRespiration.ino` and upload it.
4. Open Serial Monitor at **115200 baud**, line ending **Newline**.
5. Send `20`, `55`, or `90` to sample the low, medium and high states. Send `demo` to run the repeatable low → high → low demonstration. Send `stop` to return to manual input.

The serial output prints the target load and smoothed load. The demo lasts 30 seconds and includes a continuous rising and falling ramp.

## What makes transitions stable

- `currentHeat` follows `targetHeat` with frame-rate-independent exponential smoothing.
- The breathing phase is accumulated with elapsed time instead of being recomputed from a changing period, so changing the load does not reset the wave.
- Serial input is parsed without blocking the light update loop.
- A small gamma correction keeps low brightness visible on camera while retaining the intended mapping.

## Verification without hardware

The Python tool in [`tools/simulate_demo.py`](tools/simulate_demo.py) uses the same mapping equations as the firmware. It writes a CSV trace and renders an MP4 preview with the three labelled reference states and a continuous rise/fall sweep:

```powershell
python tools/simulate_demo.py
```

The generated files are `docs/demo-trace.csv` and `docs/continuous-load-demo.mp4`. The preview validates the software mapping only; the physical LED still needs to be tested after the hardware is purchased.

## Mapping

| Signal | Low (20) | Medium (55) | High (90) |
| --- | ---: | ---: | ---: |
| Colour | warm white | warm orange | orange-red |
| Base brightness | 38% | 61% | 84% |
| Breathing period | 5.1 s | 3.5 s | 2.0 s |

The firmware accepts every value between 0 and 100, so the three states are reference points in one continuous response.



