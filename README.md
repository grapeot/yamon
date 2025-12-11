# Yamon - Mac System Monitor

A modern, real-time system monitoring tool for macOS, featuring a web-based interface built with FastAPI backend and React frontend. Yamon provides comprehensive monitoring of CPU, Memory, Network, GPU, ANE (Apple Neural Engine), and Power metrics with beautiful historical charts.

## Features

- **Real-time Monitoring**: Live updates via WebSocket for all system metrics
- **Historical Charts**: Visualize up to 2 minutes of historical data with smooth, responsive charts
- **Web-based UI**: Modern, responsive web interface built with React and ECharts
- **Pure Python Implementation**: Uses Python `ctypes` to directly access macOS native APIs (IOReport, SMC) - **no sudo required**
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
  - **IOReport API** (Python ctypes implementation) for Apple Silicon power metrics - no sudo required
  - **SMC API** (Python ctypes implementation) for system total power - no sudo required
  - `powermetrics` as fallback for Apple Silicon metrics (requires sudo)
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
│   │   ├── ioreport.py       # IOReport API implementation (Python ctypes)
│   │   └── smc.py            # SMC API implementation (Python ctypes)
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

**Note**: Yamon uses **pure Python implementation** with `ctypes` to access macOS native APIs (IOReport and SMC) directly, eliminating the need for `sudo` privileges. This is a Python port of the approach used by tools like `mactop` and `macmon`.

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

Start the production server:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
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
  - `psutil`: Cross-platform CPU, Memory, Network metrics
  - **IOReport API** (Python ctypes): Apple Silicon CPU, GPU, ANE, and DRAM power consumption - **no sudo required**
  - **SMC API** (Python ctypes): System total power (PSTR) via IOKit - **no sudo required**
  - `powermetrics`: Fallback for Apple Silicon metrics (requires sudo)
  - `ioreg`: Fallback for GPU usage

**Implementation**: Yamon uses pure Python with `ctypes` to directly call macOS native APIs (IOReport and SMC frameworks), similar to how `mactop` (Go) and `macmon` (Rust) access these APIs. This Python implementation provides the same functionality without requiring root privileges.

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

1. **Check IOReport API**: Verify IOReport framework is available (should be available on macOS by default)
2. **Check Apple Silicon**: Ensure you're running on Apple Silicon Mac (ARM64)
3. **Debug mode**: Enable debug logging in the backend to see detailed error messages:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8001
   # Check stderr for debug messages
   ```
4. **Fallback to powermetrics**: If IOReport fails, the system will fallback to `powermetrics` (requires sudo)

### SMC API Errors

If system power shows "N/A":

1. **Check IOKit**: Ensure macOS IOKit framework is available (should be available by default)
2. **Debug mode**: Enable debug logging in the backend to see detailed error messages
3. **Permissions**: SMC API should work without sudo, but if it fails, check macOS security settings

### Frontend Not Connecting

1. **Check backend**: Ensure backend is running on the correct port
2. **Check proxy**: Verify Vite proxy configuration in `frontend/vite.config.ts`
3. **Check CORS**: Ensure CORS is enabled in FastAPI (should be enabled by default)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
