import logging

logger = logging.getLogger("task-service.log")
logging.basicConfig(level=logging.INFO)


async def write_log(task_json: dict):
    logger.info(f"[LOG] Task создана: {task_json}")
