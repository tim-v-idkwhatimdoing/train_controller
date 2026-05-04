# train_controller
Code to control a LEGO Duplo train via a USB gamepad controller over Bluetooth.

## Hardware
- LEGO Duplo Steam Train (10874)
- SAFFUN 2.4 GHz Wireless USB SNES-style Controller

## Requirements

### System dependencies
- Python 3.10
- hidapi: `brew install hidapi`

### Python dependencies
- `curio`
- `bricknil`
- `hidapi`

## Setup

```bash
# Install Python 3.10 if needed
brew install python@3.10

# Create and activate a virtual environment
/opt/homebrew/bin/python3.10 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install curio bricknil hidapi
```

## Running

Make sure the LEGO train hub is powered on and the USB gamepad is connected, then:

```bash
source .venv/bin/activate
cd usb_control
python3 main.py
```

## Controls

| Input | Action |
|-------|--------|
| Up | Forward |
| Down | Reverse |
| Left Trigger | Toggle cruise control (forward) |
| Right Trigger | Toggle cruise control (reverse) |
| Left / Right | Cycle LED color |
| Red | Emergency stop |
| Blue | Horn |
| Green | Steam sound |
| Yellow | Station sound |
