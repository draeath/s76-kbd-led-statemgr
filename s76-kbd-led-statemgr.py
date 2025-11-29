#!/usr/bin/env python3
# pylint: disable=invalid-name

"""Manages System76 keyboard backlight state across power events."""

import argparse
import json
import os
import pathlib
import re
from typing import Any


def read_configuration() -> dict:
    """Reads configuration from disk, falling back to defaults."""
    configuration_paths = [
        pathlib.Path("/usr/local/etc/s76-kbd-led-statemgr.json"),
        pathlib.Path("/etc/s76-kbd-led-statemgr.json"),
    ]
    default_config = {
        "brightness": {
            "path": "/sys/class/leds/system76_acpi::kbd_backlight/brightness",
            "default": "48",
        },
        "color": {
            "path": "/sys/class/leds/system76_acpi::kbd_backlight/color",
            "default": "FF0000",
        },
        "state_path": "/var/lib/s76-kbd-led-statemgr/state.json",
    }
    configuration = None
    for config_path in configuration_paths:
        try:
            with open(config_path, "rt", encoding="utf-8") as config_file:
                configuration = json.load(config_file)
            break
        except (OSError, json.JSONDecodeError):
            pass
    return configuration if configuration is not None else default_config


def check_valid_str(value: Any, source: str = None) -> None:
    """Raises RuntimeError if a value is not a non-empty string."""
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Invalid value read from '{source}'")


def read_state(configuration: dict) -> dict:
    """Reads keyboard state from disk, falling back to defaults."""
    default_brightness = configuration["brightness"]["default"]
    default_color = configuration["color"]["default"]
    default_state = {"brightness": default_brightness, "color": default_color}
    state_path = configuration["state_path"]

    try:
        with open(state_path, "rt", encoding="utf-8") as state_file:
            state = json.load(state_file)
            brightness_ok = 0 <= int(state["brightness"]) <= 255
            color_ok = re.fullmatch(r"^(00|FF){3}$", state["color"])
            if brightness_ok and color_ok:
                return state
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        pass  # Fall through to return default state

    return default_state


def write_state(configuration: dict, state: dict, is_root: bool) -> None:
    """Writes keyboard state to disk."""
    state_path = configuration["state_path"]
    if not is_root:
        pretty_state = json.dumps(state, indent=2)
        print(f"DRY-RUN: Would write state to '{state_path}':\n{pretty_state}")
        return
    pathlib.Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "wt", encoding="utf-8") as out_file:
        json.dump(state, out_file, indent=2)
        out_file.write("\n")


def apply_state(configuration: dict, state: dict, is_root: bool) -> None:
    """Applies keyboard state to the system."""
    brightness_path = configuration["brightness"]["path"]
    color_path = configuration["color"]["path"]
    if not is_root:
        print(
            f"DRY-RUN: Would write brightness '{state['brightness']}' to '{brightness_path}'"
        )
        print(f"DRY-RUN: Would write color '{state['color']}' to '{color_path}'")
        return
    with open(brightness_path, "wt", encoding="utf-8") as brightness_file:
        brightness_file.write(state["brightness"] + "\n")
    with open(color_path, "wt", encoding="utf-8") as color_file:
        color_file.write(state["color"] + "\n")


def do_pre(configuration: dict, is_root: bool) -> None:
    """Reads current keyboard state and saves it before a power event."""
    with open(
        configuration["brightness"]["path"], "rt", encoding="utf-8"
    ) as brightness_file:
        brightness = brightness_file.readline().strip()
        check_valid_str(brightness, source=brightness_file.name)
    with open(configuration["color"]["path"], "rt", encoding="utf-8") as color_file:
        color = color_file.readline().strip()
        check_valid_str(color, source=color_file.name)
    write_state(configuration, {"brightness": brightness, "color": color}, is_root)


def do_post(configuration: dict, is_root: bool) -> None:
    """Applies saved keyboard state after a power event."""
    state = read_state(configuration)
    apply_state(configuration, state, is_root)


def main() -> None:
    """Parses arguments and runs the pre or post action."""
    parser = argparse.ArgumentParser(
        description="https://github.com/draeath/s76-kbd-led-statemgr/blob/master/README.md",
    )
    parser.add_argument(
        "transition",
        type=str,
        help="The [pre|post] keyword from systemd-suspend.service",
        choices=["pre", "post"],
    )
    args = parser.parse_known_args()[0]
    configuration = read_configuration()
    is_root = os.geteuid() == 0

    if args.transition == "pre":
        do_pre(configuration, is_root)
    elif args.transition == "post":
        do_post(configuration, is_root)


if __name__ == "__main__":
    main()
