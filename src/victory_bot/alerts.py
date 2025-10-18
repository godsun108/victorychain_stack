import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")


def send_discord_alert(content: str):
    if not DISCORD_WEBHOOK:
        logger.debug("Discord webhook not configured.")
        return False
    try:
        payload = {"content": content}
        resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        return resp.ok
    except Exception as e:
        logger.error("send_discord_alert failed: %s", e)
        return False


def send_slack_alert(text: str):
    if not SLACK_WEBHOOK:
        logger.debug("Slack webhook not configured.")
        return False
    try:
        payload = {"text": text}
        resp = requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
        return resp.ok
    except Exception as e:
        logger.error("send_slack_alert failed: %s", e)
        return False


def send_critical_alert(message: str):
    ok = False
    if DISCORD_WEBHOOK:
        ok = send_discord_alert(message) or ok
    if SLACK_WEBHOOK:
        ok = send_slack_alert(message) or ok
    if not ok:
        logger.warning("No alert delivered: %s", message)
    return ok
