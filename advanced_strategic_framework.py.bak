#!/usr/bin/env python3
"""
🧠 ADVANCED STRATEGIC TRADING FRAMEWORK
=======================================
Enterprise-level trading strategy with sophisticated portfolio management,
risk optimization, and intelligent decision-making systems.
"""

import json
import os
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
import pandas as pd

from src.victory_bot import trailing as trailing_module
from src.victory_bot import execution as execution_module
from src.victory_bot import alerts as alerts_module

# Centralized config (from .env)
TRAILING_STOP_ACTIVATION_PCT = float(os.getenv("TRAILING_STOP_ACTIVATION_PCT", 0.50))
TRAILING_STOP_PCT = float(os.getenv("TRAILING_STOP_PCT", 0.10))
MIN_PROFIT_EXIT_PCT = float(os.getenv("MIN_PROFIT_EXIT_PCT", 0.05))
MAX_POSITION_SIZE_USD = float(os.getenv("MAX_POSITION_SIZE", 10000.0))
VICTORYBOT_STOP_LOSS_PCT = float(os.getenv("VICTORYBOT_STOP_LOSS_PCT", 2.0)) / 100.0
DAILY_LOSS_LIMIT = float(os.getenv("DAILY_LOSS_LIMIT", 1000.0))

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enums
class MarketRegime(Enum):
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"

class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ULTRA_AGGRESSIVE = "ultra_aggressiv
