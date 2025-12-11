# Yamon - Mac System Monitor

A modern, real-time system monitoring tool for macOS, featuring a web-based interface built with FastAPI backend and React frontend. Yamon provides comprehensive monitoring of CPU, Memory, Network, GPU, ANE (Apple Neural Engine), and Power metrics with beautiful historical charts.

## Features

- **Real-time Monitoring**: Live updates via WebSocket for all system metrics
- **Historical Charts**: Visualize up to 2 minutes of historical data with smooth, responsive charts
- **Web-based UI**: Modern, responsive web interface built with React and ECharts
- **Apple Silicon Support**: Deep integration with Apple Silicon hardware metrics including:
  - Per-core CPU usage (P-cores and E-cores distinction)
  - GPU usage and frequency
  - ANE (Apple Neural Engine) usage
  - Component-level power consumption (CPU, GPU, ANE)
  - System total power via SMC API
- **Cross-platform Core**: Uses `psutil` for cross-platform CPU, Memory, and Network metrics

## Architecture

Yamon follows a client-server architecture:

- **Backend**: FastAPI-based Python server that collects system metrics and serves the frontend
- **Frontend**: React + Vite application that displays metrics in real-time
- **Data Collection**: 
  - `psutil` for CPU, Memory, and Network metrics
  - `powermetrics` for Apple Silicon power and GPU metrics (requires sudo)
  - SMC API for system total power (requires sudo)
  - `ioreg` as fallback for GPU usage

## Project Structure

```
.
├── backend/                  # FastAPI backend
│   ├── api/                  # API endpoints
│   │   ├── metrics.py        # REST API for metrics
│   │   └── websocket.py      # WebSocket endpoint
│   ├── collectors/           # Data collection logic
│   │   ├── collector.py      # Main metrics collector
│   │   ├── apple_api.py      # Apple Silicon specific metrics
│   │   └── smc.py            # SMC API for system power
│   ├── history.py            # Historical data management
│   ├── main.py               # FastAPI application entry point
│   └── static/               # Static files (generated from frontend build)
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── components/       # React chart components
│   │   │   ├── CpuChart.tsx
│   │   │   ├── MemoryChart.tsx
│   │   │   ├── NetworkChart.tsx
│   │   │   ├── PowerChart.tsx
│   │   │   ├── GpuChart.tsx
│   │   │   └── AneChart.tsx
│   │   ├── App.tsx           # Main application component
│   │   └── ...
│   └── package.json
├── scripts/                  # Build and deployment scripts
│   ├── run_backend.sh
│   ├── run_frontend.sh
│   └── build_frontend.sh
└── requirements.txt          # Python dependencies

```

## Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **Node.js 18+** (for frontend development)
- **macOS** (for Apple Silicon metrics; Intel Macs will show basic metrics only)
- **sudo privileges** (required for Apple Silicon power and GPU metrics)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd yamon
```

### 2. Backend Setup

Create a virtual environment (using `uv` if available, or standard `venv`):

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate

# Or using standard venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install Python dependencies:

```bash
# Using uv
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## Development

### Running the Backend

Start the FastAPI backend server:

```bash
# From project root
python -m uvicorn backend.main:app --reload --port 8001
```

Or use the convenience script:

```bash
./scripts/run_backend.sh 8001
```

**Note**: Currently, Apple Silicon metrics (GPU, ANE, Power) require `sudo` because we use `powermetrics` command-line tool. 

**Future Improvement**: We plan to migrate to IOReport API (like `mactop` does) which doesn't require sudo. IOReport API is a user-level API provided by macOS that can access CPU, GPU, ANE, and DRAM power consumption without root privileges.

For now, run with `sudo`:

```bash
sudo python -m uvicorn backend.main:app --reload --port 8001
```

The backend will be available at:
- **API**: http://localhost:8001/api/metrics
- **WebSocket**: ws://localhost:8001/ws/metrics
- **API Docs**: http://localhost:8001/docs

### Running the Frontend

In a separate terminal, start the Vite development server:

```bash
./scripts/run_frontend.sh
```

Or manually:

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:5173

The Vite dev server is configured to proxy API and WebSocket requests to the backend automatically.

## Production Build

### 1. Build Frontend

Build the frontend and copy static files to the backend:

```bash
./scripts/build_frontend.sh
```

Or manually:

```bash
cd frontend
npm run build
cd ..
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
```

### 2. Run Production Server

Start the production server (with sudo for Apple Silicon metrics):

```bash
sudo python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

The application will be available at http://localhost:8001

## Metrics Details

### CPU Metrics
- **Per-core usage**: Individual CPU core utilization
- **P-core / E-core distinction**: Separate tracking for performance and efficiency cores on Apple Silicon
- **Historical data**: 2 minutes of per-core usage history

### Memory Metrics
- **Total, Used, Available**: Memory statistics in bytes
- **Percentage usage**: Real-time memory utilization percentage
- **Historical chart**: Area chart showing memory usage over time

### Network Metrics
- **Upload/Download rates**: Real-time network traffic in bytes per second
- **Dual-direction chart**: Upload (bottom-up) and Download (top-down) visualization
- **Auto-scaling**: Automatic unit conversion (B, KB, MB, GB)

### Power Metrics (Apple Silicon)
- **CPU Power**: CPU power consumption in watts
- **GPU Power**: GPU power consumption in watts
- **ANE Power**: Apple Neural Engine power consumption in watts
- **System Power**: Total system power via SMC API (PSTR)
- **Stacked chart**: Visual representation of component power breakdown

### GPU Metrics (Apple Silicon)
- **GPU Usage**: GPU utilization percentage
- **Historical chart**: Area chart showing GPU usage over time

### ANE Metrics (Apple Silicon)
- **ANE Usage**: Apple Neural Engine utilization percentage
- **Historical chart**: Area chart showing ANE usage over time

## Technical Details

### Data Collection

- **Update Frequency**: 1 second intervals
- **History Buffer**: 120 data points (2 minutes at 1s interval)
- **Collection Methods**:
  - `psutil`: Cross-platform CPU, Memory, Network
  - `powermetrics`: Apple Silicon power and GPU metrics (requires sudo)
  - SMC API: System total power via IOKit (requires sudo)
  - `ioreg`: Fallback for GPU usage

### API Endpoints

- `GET /api/metrics`: Get current system metrics
- `GET /api/history`: Get historical metrics data
- `WebSocket /ws/metrics`: Real-time metrics stream

### Frontend Technologies

- **React 18+**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **ECharts**: Powerful charting library
- **WebSocket**: Real-time data updates

## Troubleshooting

### Apple Silicon Metrics Not Showing

If GPU, ANE, or Power metrics show as "N/A" or 0:

1. **Check sudo**: Ensure the backend is running with `sudo`
2. **Check powermetrics**: Verify `powermetrics` is available:
   ```bash
   which powermetrics
   ```
3. **Check permissions**: Some metrics require root privileges

### SMC API Errors

If system power shows "N/A":

1. **Run with sudo**: SMC API requires root privileges
2. **Check IOKit**: Ensure macOS IOKit framework is available
3. **Debug mode**: Enable debug logging in the backend to see detailed error messages

### Frontend Not Connecting

1. **Check backend**: Ensure backend is running on the correct port
2. **Check proxy**: Verify Vite proxy configuration in `frontend/vite.config.ts`
3. **Check CORS**: Ensure CORS is enabled in FastAPI (should be enabled by default)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
