import logging
from datetime import datetime

logger = logging.getLogger("notifications")
logging.basicConfig(level=logging.INFO)

notifications_log = []


def record_notification(task: dict):
    entry = {
        "received_at": datetime.utcnow().isoformat(),
        "task_id": str(task["id"]),
        "title": task["title"],
    }
    notifications_log.append(entry)
    logger.info(f"[NOTIFY] Пользователю отправлено уведомление о задаче: {task['title']} (id={task['id']})")
    return entry
