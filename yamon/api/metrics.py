"""HTTP metric endpoints using the same samples as the WebSocket."""

import asyncio

from fastapi import APIRouter

from yamon.api import websocket
from yamon.api.payload import metric_payload
from yamon.summary import summary_store

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    await websocket.start_background_collector()
    metrics = websocket.latest_metrics()
    if metrics is None:
        async with websocket._collection_condition:
            await websocket._collection_condition.wait_for(lambda: websocket.latest_metrics() is not None)
            metrics = websocket.latest_metrics()
    return metric_payload(metrics)


@router.get("/summary")
async def get_summary():
    return await asyncio.to_thread(summary_store.get_windows, [3600, 86400, 3 * 86400, 7 * 86400, 14 * 86400])


@router.get("/history")
async def get_history():
    h = websocket.history
    return {
        "cpu_percent": h.cpu_percent.get_values(),
        "memory_percent": h.memory_percent.get_values(),
        "network_sent_rate": h.network_sent_rate.get_values(),
        "network_recv_rate": h.network_recv_rate.get_values(),
        "cpu_power": h.cpu_power.get_values(),
        "gpu_power": h.gpu_power.get_values(),
        "ane_power": h.ane_power.get_values(),
        "system_power": h.system_power.get_values(),
        "gpu_usage": h.gpu_usage.get_values(),
        "cpu_temp_c": h.cpu_temp_c.get_values(),
        "gpu_temp_c": h.gpu_temp_c.get_values(),
    }
