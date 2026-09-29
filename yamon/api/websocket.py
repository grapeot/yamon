"""Shared background collector and live WebSocket feed."""

import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from yamon.api.payload import metric_payload
from yamon.collectors.collector import MetricsCollector, SystemMetrics
from yamon.history import MetricsHistory
from yamon.summary import summary_store

router = APIRouter()
collector = MetricsCollector()
history = MetricsHistory(max_size=120)
_latest_metrics: Optional[SystemMetrics] = None
_metrics_lock = asyncio.Lock()
_collection_task: Optional[asyncio.Task] = None
_collection_condition = asyncio.Condition()
_sample_id = 0


async def _background_collector():
    global _latest_metrics, _sample_id
    loop = asyncio.get_running_loop()
    while True:
        started = loop.time()
        try:
            metrics = await asyncio.to_thread(collector.collect)
            history.add_metrics(metrics)
            await asyncio.to_thread(summary_store.tick, metrics)
            async with _collection_condition:
                _latest_metrics = metrics
                _sample_id += 1
                _collection_condition.notify_all()
            # Aim for one new sample per second. A slow collector determines
            # the actual rate, which clients can read from sample timestamps.
            await asyncio.sleep(max(0.0, 1.0 - (loop.time() - started)))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"Background collector error: {exc}")
            await asyncio.sleep(0.5)


async def start_background_collector():
    global _collection_task
    if _collection_task is None or _collection_task.done():
        _collection_task = asyncio.create_task(_background_collector())


def latest_metrics():
    return _latest_metrics


@router.websocket("/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    await start_background_collector()
    last_id = 0
    try:
        while True:
            async with _collection_condition:
                await _collection_condition.wait_for(lambda: _sample_id > last_id)
                last_id = _sample_id
                metrics = _latest_metrics
            if metrics is not None:
                await websocket.send_json(metric_payload(metrics))
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print(f"WebSocket error: {exc}")
