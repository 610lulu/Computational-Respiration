# Hardware purchase and bench checklist

The physical hardware has not been purchased yet. Use this exact baseline so the firmware and wiring match the first build:

## Buy

- **ESP32 DevKit V1, ESP32-WROOM-32, 30-pin** (the common CP2102 or CH340 USB versions are both fine).
- **One 4-pin RGB LED module, common cathode, with onboard resistors**. Search terms: `KY-016 RGB LED module common cathode` or an equivalent 3.3 V module.
- USB data cable, breadboard and male-to-female jumper wires.

Avoid a bare RGB LED for the first test unless you also buy three 220–330 Ω resistors. Avoid a WS2812/NeoPixel strip for this firmware: it uses three independent PWM channels instead of the one-wire addressable protocol.

## Check before powering

1. Identify the module's common pin with its product diagram or a multimeter. The baseline is common cathode, connected to **GND**.
2. Confirm the module has resistors. If it does not, put one 220–330 Ω resistor in series with each R, G and B wire.
3. Confirm that the ESP32 board's 3V3 and GPIO pins are used; do not feed 5 V into an LED GPIO.
4. Wire R → GPIO 25, G → GPIO 26, B → GPIO 27, common cathode → GND.
5. Upload the firmware and send `20` in Serial Monitor. If the colour is inverted, power down, verify the module type and set `COMMON_ANODE` only when the hardware is truly common anode.

## First bench test

Before mounting the light, test the three reference commands in a dim room:

```text
20   low: warm, dim, slow
55   medium: warmer and brighter
90   high: orange-red, bright, faster
```

Then send `demo`. The firmware runs low, medium and high reference states, followed by a continuous rise/fall sweep. Record the physical result after the board and module arrive; the MP4 in `docs/continuous-load-demo.mp4` is the software preview, not a camera recording of the LED.

