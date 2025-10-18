from datetime import datetime


def stop_trading_alert(reason: str):
    ts = datetime.utcnow().isoformat()
    return f"[VICTORYBOT - STOP_TRADING] {ts} - Manual stop triggered. Reason: {reason}"


def daily_loss_alert(realized_losses: float, limit: float):
    ts = datetime.utcnow().isoformat()
    return (
        f"[VICTORYBOT - DAILY_LOSS] {ts} - Daily loss limit reached: "
        f"${realized_losses:,.2f} >= ${limit:,.2f}. Trading halted."
    )


def order_failure_alert(symbol: str, side: str, details: str):
    ts = datetime.utcnow().isoformat()
    return f"[VICTORYBOT - ORDER_FAILURE] {ts} - {side.upper()} failed for {symbol}. Details: {details}"


def large_loss_alert(symbol: str, loss_usd: float, trade_id: str = ""):
    ts = datetime.utcnow().isoformat()
    return f"[VICTORYBOT - LARGE_LOSS] {ts} - Large loss on {symbol}: ${loss_usd:,.2f}. Trade: {trade_id}"


def send_alert_via_module(message: str, use_alerts_module=True):
    """
    Helper: if your alerts module is configured, forward message to it.
    """
    if use_alerts_module:
        try:
            from src.victory_bot import alerts as alerts_module

            alerts_module.send_critical_alert(message)
            return True
        except Exception:
            return False
    return False
