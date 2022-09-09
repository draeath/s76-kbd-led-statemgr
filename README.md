# s76-kbd-led-statemgr

A crappy attempt to persist keyboard backlight state across power states (reboot, hibernate, suspend etc).

## Description

On my recently aquired System76 Darter Pro (darp8) I found that, if not using Pop\_OS!, the keyboard backlight state is not persistent through shutdowns.

Fortunately, `/sys/class/leds/system76_acpi::kbd_backlight/` provides a simple text-file based means to read and write state.

## Getting Started

### Dependencies

* A modern version of python3, available in systemd's PATH. Developed with 3.10.6 but will likely work with other versions!

### Installation

* Place the python script somewhere, with executable permissions. For safety, prohibit modification by regular users.
* Symlink the script under `/usr/lib/systemd/system-sleep/` as per [systemd-suspend.service](https://www.freedesktop.org/software/systemd/man/systemd-suspend.service.html)
* Copy s76-kbd-led-statemgr.service to `/etc/systemd/system`, run `systemd daemon-reload && systemctl enable --now s76-kbd-led-statemgr.service`

### Execution

* Once set up, [systemd will run the program as necessary.](https://www.freedesktop.org/software/systemd/man/systemd-suspend.service.html). Specifically, it takes one argument, the the word 'pre' or 'post.' Other values or additional arguments are silently discarded.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](./LICENSE.txt) file for details
