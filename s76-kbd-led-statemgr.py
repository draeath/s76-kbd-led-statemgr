#!/usr/bin/env python3

import json
import pathlib

default_config = {
    "basepath": "/sys/class/leds/",
    "brightness": {"path": "system76_acpi::kbd_backlight/brightness", "enable": True},
    "color": {"path": "system76_acpi::kbd_backlight/color", "enable": True},
}
