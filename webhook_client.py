import asyncio
import logging
import httpx

logger = logging.getLogger("task-service")
NOTIFICATION_URL = "http://localhost:8001/api/webhooks/task_created"

retry_queue: asyncio.Queue() = asyncio.Queue()

async def notify_task_created(task:dict):
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.post(NOTIFICATION_URL, json=task)
            response.raise_for_status()
            logger.info(f"webhook доставлен для {task['id']}")
    except httpx.RequestError as e:
        logger.error(f"Ошибка при доставке webhook для {task['id']}: {e}")
        await retry_queue.put(task)

async def retry_worker(interval_seconds: int = 5, max_attemps: int = 5):
    while True:
        await asyncio.sleep(interval_seconds)
        pending = []
        while not retry_queue.empty():
            pending.append(await retry_queue.get())
        for task in pending:
            attemps = task.setdefault("attemps", 0) + 1
            task["_attemps"] = attemps
            try:
                async with httpx.AsyncClient(timeout=3) as client:
                    response = await client.post(NOTIFICATION_URL, json=task)
                    response.raise_for_status()
                logger.info(f"webhook доставлен для {task['id']} после {attemps} попыток")
            except httpx.HTTPError:
                if attemps < max_attemps:
                    await retry_queue.put(task)
                else:
                    logger.error(f"Ошибка при доставке webhook для {task['id']}: {e}. Превышено количество попыток ({max_attemps})")