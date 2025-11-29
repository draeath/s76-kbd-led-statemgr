use regex::Regex;
use serde::{Deserialize, Serialize};
use std::env;
use std::fs::{self, File};
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Deserialize)]
struct Config {
    brightness: DeviceConfig,
    color: DeviceConfig,
    state_path: PathBuf,
}

#[derive(Debug, Deserialize)]
struct DeviceConfig {
    path: PathBuf,
    default: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct State {
    brightness: String,
    color: String,
}

fn read_configuration() -> Config {
    let config_paths = [
        "/usr/local/etc/s76-kbd-led-statemgr.json",
        "/etc/s76-kbd-led-statemgr.json",
    ];

    for path in &config_paths {
        if let Ok(file) = File::open(path) {
            if let Ok(config) = serde_json::from_reader(file) {
                return config;
            }
        }
    }

    // Default configuration if no file is found or is invalid
    Config {
        brightness: DeviceConfig {
            path: "/sys/class/leds/system76_acpi::kbd_backlight/brightness".into(),
            default: "48".to_string(),
        },
        color: DeviceConfig {
            path: "/sys/class/leds/system76_acpi::kbd_backlight/color".into(),
            default: "FF0000".to_string(),
        },
        state_path: "/var/lib/s76-kbd-led-statemgr/state.json".into(),
    }
}

fn read_state(config: &Config) -> State {
    let default_state = State {
        brightness: config.brightness.default.clone(),
        color: config.color.default.clone(),
    };

    let Ok(file) = File::open(&config.state_path) else {
        return default_state;
    };

    let mut state: State = match serde_json::from_reader(file) {
        Ok(s) => s,
        Err(_) => return default_state,
    };

    // Validate brightness
    if state.brightness.parse::<u8>().is_err() {
        state.brightness = config.brightness.default.clone();
    }

    // Validate color
    let color_regex = Regex::new(r"^(00|FF){3}$").unwrap();
    if !color_regex.is_match(&state.color) {
        state.color = config.color.default.clone();
    }

    state
}

fn write_state(config: &Config, state: &State) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(parent) = config.state_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let mut file = File::create(&config.state_path)?;
    let json_string = serde_json::to_string_pretty(state)?;
    file.write_all(json_string.as_bytes())?;
    file.write_all(b"\n")?;

    Ok(())
}

fn apply_state(config: &Config, state: &State) -> Result<(), Box<dyn std::error::Error>> {
    fs::write(&config.brightness.path, format!("{}\n", state.brightness))?;
    fs::write(&config.color.path, format!("{}\n", state.color))?;
    Ok(())
}

fn do_pre(config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    let brightness = fs::read_to_string(&config.brightness.path)?
        .trim()
        .to_string();
    if brightness.is_empty() {
        return Err(format!(
            "Invalid empty value read from '{}'",
            config.brightness.path.display()
        )
        .into());
    }

    let color = fs::read_to_string(&config.color.path)?.trim().to_string();
    if color.is_empty() {
        return Err(format!(
            "Invalid empty value read from '{}'",
            config.color.path.display()
        )
        .into());
    }

    let state = State { brightness, color };
    write_state(config, &state)
}

fn do_post(config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    let state = read_state(config);
    apply_state(config, &state)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let transition = args
        .get(1)
        .ok_or("Missing required argument: must be 'pre' or 'post'")?;

    let config = read_configuration();

    match transition.as_str() {
        "pre" => do_pre(&config),
        "post" => do_post(&config),
        _ => Err(format!("Invalid argument '{}', must be 'pre' or 'post'", transition).into()),
    }
}
