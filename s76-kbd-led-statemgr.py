#!/usr/bin/env python3

import argparse
import json
import pathlib
import re


def read_configuration() -> dict:
    configuration_paths = [
        pathlib.PosixPath("/usr/local/etc/s76-kbd-led-statemgr.json"),
        pathlib.PosixPath("/etc/s76-kbd-led-statemgr.json"),
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
        # noinspection PyBroadException
        try:
            with open(config_path, "rt") as config_file:
                configuration = json.load(config_file)
            break
        except Exception:
            pass
    return configuration if configuration is not None else default_config


def check_valid_str(value, source: str = None) -> None:
    if (type(value) is not str) or (len(value) == 0):
        raise RuntimeError(f"Invalid value read from '{source}'")


def read_state(configuration: dict) -> dict:
    default_brightness = configuration["brightness"]["default"]
    default_color = configuration["color"]["default"]
    state_path = configuration["state_path"]
    # noinspection PyBroadException
    try:
        with open(state_path, "rt") as state_file:
            state = json.load(state_file)
            if not 0 <= int(state["brightness"]) <= 255:
                state["brightness"] = default_brightness
            if not re.fullmatch(r"^(00|FF){3}$", state["color"]):
                state["color"] = default_color
    except Exception:
        state = {"brightness": default_brightness, "color": default_color}
    return state


def write_state(configuration: dict, state: dict):
    state_path = configuration["state_path"]
    pathlib.PosixPath(state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "wt") as out_file:
        json.dump(state, out_file, indent=2)
        out_file.write("\n")
    return


def apply_state(configuration: dict, state: dict):
    brightness_path = configuration["brightness"]["path"]
    color_path = configuration["color"]["path"]
    with open(brightness_path, "at") as brightness_file:
        brightness_file.write(state["brightness"] + "\n")
    with open(color_path, "at") as color_file:
        color_file.write(state["color"] + "\n")


def do_pre(configuration: dict) -> None:
    with open(configuration["brightness"]["path"], "rt") as brightness_file:
        brightness = brightness_file.readline().strip()
        check_valid_str(brightness, source=brightness_file.name)
    with open(configuration["color"]["path"], "rt") as color_file:
        color = color_file.readline().strip()
        check_valid_str(color, source=color_file.name)
    write_state(configuration, {"brightness": brightness, "color": color})


def do_post(configuration: dict) -> None:
    state = read_state(configuration)
    apply_state(configuration, state)


def main():
    parser = argparse.ArgumentParser(
        description="https://github.com/draeath/s76-kbd-led-statemgr/blob/master/README.md",
    )
    parser.add_argument(
        "transition",
        type=str,
        help="The [pre|post] keyword from systemd-suspend.service",
    )
    args = parser.parse_known_args()[0]
    if args.transition not in ["pre", "post"]:
        raise ValueError(f"Invalid argument '{args.transition}'")
    configuration = read_configuration()

    if args.transition == "pre":
        do_pre(configuration)
    elif args.transition == "post":
        do_post(configuration)


if __name__ == "__main__":
    main()
