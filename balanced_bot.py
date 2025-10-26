from core.logger import get_logger
import os, time

log = get_logger("BalancedBot")

def get_duration_hours() -> float:
    """
    Unified duration source:
    - Prefer env DURATION_HOURS (set by launcher)
    - Fallback to 8.0 if not provided or invalid
    """
    try:
        return float(os.getenv("DURATION_HOURS", "8"))
    except Exception:
        return 8.0

SAFE_MODE = os.getenv("SAFE_MODE", "false").lower() == "true"
duration = get_duration_hours()
log.info("Balanced bot started. SAFE_MODE=%s duration_hours=%.2f", SAFE_MODE, duration)
end_time = time.time() + duration * 3600.0

# ...existing code...