# Yamon - Mac System Monitor

A modern system monitoring tool for macOS, built with FastAPI backend and React frontend.

## Features

- **Real-time monitoring**: CPU, Memory, Network, GPU, ANE (Apple Neural Engine), and Power metrics
- **Historical charts**: Visualize system metrics over time
- **Web-based UI**: Modern, responsive web interface
- **Apple Silicon support**: Deep integration with Apple Silicon hardware metrics

## Project Structure

```
yamon/
├── backend/              # FastAPI backend
│   ├── api/              # API endpoints
│   ├── collectors/       # Data collection logic
│   ├── main.py           # FastAPI application
│   └── static/           # Static files (generated)
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   └── ...
│   └── ...
└── scripts/              # Build and deployment scripts
```

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- macOS (for Apple Silicon metrics)

### Backend Setup

1. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start backend server:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000/api/metrics
- WebSocket: ws://localhost:8000/ws/metrics
- API Docs: http://localhost:8000/docs

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Production Build

1. Build frontend:
```bash
cd frontend
npm run build
```

2. Copy static files to backend:
```bash
./scripts/build.sh
```

3. Start production server:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The application will be available at http://localhost:8000

## Apple Silicon Metrics

For GPU, ANE, and power metrics, you may need to run with `sudo`:

```bash
sudo python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## License

MIT
