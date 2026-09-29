# Yamon 🍊

**Beautiful, In-Depth System Monitoring for macOS.**

Yamon is a modern system monitor engineered specifically for Apple Silicon. It goes beyond standard CPU and RAM metrics to reveal the true heartbeat of your Mac — from Neural Engine activity to precise component-level power consumption — all displayed in an elegant, real-time web interface.

![Yamon Screenshot](docs/screenshot.jpg)

## ✨ Features

### 🚀 Deep Apple Silicon Integration
Unlock metrics that standard tools often hide:
- **Total System Power**: SMC power reading in watts when the sensor is available.
- **Power Breakdown**: Estimated CPU, GPU, and Neural Engine power in watts.
- **Neural Engine (ANE)**: Estimated power is shown when available. Current samplers do not provide ANE utilization, so that reading remains unavailable.
- **GPU Frequency & Usage**: GPU frequency and hardware active-time percentage when available.
- **CPU & GPU Temperature**: Average of available SMC temperature sensors in °C, with a live two-minute chart.

### ⚡️ Real-Time & Responsive
- **Live Sampling**: WebSockets send each new sample as it arrives, normally about once per second.
- **Historical Context**: Interactive charts visualize the last 2 minutes of performance data.
- **Modern UI**: Built with React, TypeScript, and ECharts for a premium, responsive aesthetic on any device.

### 🛠️ Native Performance, Pure Python
- **Native APIs via ctypes**: Directly interfaces with macOS `IOReport` and `SMC` private frameworks.
- **No Heavy Dependencies**: Pure Python implementation without the need for compiling Rust or C/C++ binaries.
- **No Sudo Required**: IOReport provides component power without root; `powermetrics` adds GPU active time and CPU/GPU frequencies when Yamon runs as root.*

## 📦 Installation

### Install from PyPI (Recommended)

The easiest way to install Yamon:

```bash
pip install yamon
```

After installation, start the monitor:

```bash
yamon
```

Visit **http://localhost:8000** to view your dashboard.

📦 **Available on PyPI**: [https://pypi.org/project/yamon/](https://pypi.org/project/yamon/)
PyPI releases may lag this repository; install from source to test unreleased changes.

### Install from Source

```bash
# Clone the repository
git clone https://github.com/grapeot/yamon.git
cd yamon

# Install in development mode
pip install -e .
```

## 📸 Usage

### Using the Installed Package (Recommended)

After installing from PyPI or source, simply run:

```bash
yamon
```

Or with custom options:

```bash
yamon --host 0.0.0.0 --port 8000 --reload
```

Yamon listens on `127.0.0.1` by default. Use `--host` only when you intend to
make the unauthenticated dashboard reachable from another device.

### Inspecting a One-Shot Sample on macOS

`powermetrics` needs administrator privileges. This command takes one sample,
writes a local JSON file, and exits; it does not start Yamon:

```bash
sudo /usr/bin/powermetrics -i 1000 -n 1 -s cpu_power,gpu_power,ane_power -f plist \
  | /usr/bin/python3 -c 'import sys,plistlib,json; raw=sys.stdin.buffer.read().strip(b"\0"); print(json.dumps(plistlib.loads(raw),default=str))' \
  > powermetrics.json
```

The `processor.cpu_power`, `processor.gpu_power`, and `processor.ane_power`
values in this plist are **milliwatts**; Yamon converts them to watts. The
`gpu.idle_ratio` field measures idle time, so Yamon displays
`(1 - idle_ratio) × 100` as GPU active time. Apple's estimated power figures
are useful for changes on one machine, not calibrated wall-outlet power.

To allow only that exact `powermetrics` command without a password on a Mac,
open a sudoers file with the validating editor:

```bash
sudo env EDITOR=/usr/bin/nano /usr/sbin/visudo -f /etc/sudoers.d/yamon-powermetrics
```

Paste the following **inside the editor, not at the shell prompt**:

```text
YOUR_USERNAME ALL=(root) NOPASSWD: /usr/bin/powermetrics -i 1000 -n 1 -s cpu_power\,gpu_power\,ane_power -f plist
```

Replace `YOUR_USERNAME` with the output of `id -un`. In nano, press `Ctrl-O`, Return,
then `Ctrl-X`. Check the rule with a noninteractive one-shot call:

```bash
sudo -n /usr/bin/powermetrics -i 1000 -n 1 -s cpu_power,gpu_power,ane_power -f plist > /dev/null
```

The backslashes before commas belong only in the sudoers rule, not in the
terminal command. This rule grants access to this one `powermetrics` command;
it does **not** make Yamon itself run as root. To use Yamon's root-only metrics,
start Yamon from an explicitly privileged launch (for example,
`sudo uv tool run yamon` when installed with uv).

### Viewing Temperatures

The Temperature chart shows separate CPU and GPU sensor averages and their
recent history. Missing or invalid sensor readings appear as unavailable, not
as 0°C. These sensors can be read without sudo on supported Macs. For an
independent one-shot check on a Mac with `macmon` installed:

```bash
macmon pipe -s 1 -i 1000 | jq '.temp'
```

These are separate CPU and GPU temperature readings in °C, not one overall
"system temperature." `powermetrics -s thermal` reports thermal pressure,
not a temperature in °C.

### Development Mode (From Source)

If you're developing from source:

```bash
# 1. Install in development mode
pip install -e .

# 2. Build Frontend (for production mode)
./build_frontend.sh

# 3. Run Backend
./run_backend.sh
```

Or run the installed command:

```bash
yamon --reload
```

### Development Mode (Separate Frontend & Backend)
For contributors who want to modify the frontend code.

```bash
# 1. Install in development mode
pip install -e .

# 2. Run Backend (Collects data)
./run_backend.sh

# 3. Run Frontend (Hot-reload dev server)
./run_frontend.sh
```
Visit **http://localhost:5173** for the development server.

## 🏗️ Architecture

Yamon bridges the gap between low-level hardware counters and high-level visualization:

1.  **Collectors (Python)**: Low-overhead bindings to Apple's private frameworks (`IOKit`, `IOReport`).
2.  **Server (FastAPI)**: Aggregates metrics and broadcasts them via efficient WebSocket streams.
3.  **Frontend (React)**: High-performance canvas rendering for dense data visualization.

## 📈 Multi-Day Averages

Yamon records per-minute aggregates of CPU, memory used, and system power to a
single JSONL file and shows rolling 3/7/14-day averages at the bottom of the dashboard.

- Data file: `~/Library/Application Support/yamon/summary.jsonl` (override the
  directory with the `YAMON_DATA_DIR` environment variable)
- Auto-rotate: rows older than 21 days are dropped on startup and hourly; a
  hard 20 MB cap drops the oldest rows if the file ever exceeds it
- Disk cost: one small append per minute (~150 KB/day)
- Averages only cover time while Yamon is running and the machine is awake

## 🔋 Power Monitoring Accuracy
Yamon reads the SMC `PSTR` key for system power when available. Component
power is estimated from `powermetrics` or IOReport over a one-second window.
These sources cover different parts of the machine, so system power is not
expected to equal the sum of CPU, GPU, and ANE power.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Note: While Yamon is designed to run without root, some deeply protected system metrics may unavailable without elevated privileges. The application will degrade gracefully in these cases.*
