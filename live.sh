#!/bin/zsh
# Live launch script for Victory Trading Bot with dashboard

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Python virtual environment not found! Exiting."
    exit 1
fi

# Set PYTHONPATH so 'victory_bot' is importable
export PYTHONPATH=$(pwd)/src

# Start the trading bot in the background
nohup python -m victory_bot.runners.live_bot > live_bot.log 2>&1 &
echo "Victory Trading Bot started (log: live_bot.log)"

# Start the Streamlit dashboard in a new terminal window
if command -v osascript > /dev/null; then
    osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\"; source venv/bin/activate; streamlit run src/victory_bot/dashboard/streamlit_dashboard.py"'
    echo "Streamlit dashboard launched in a new Terminal window."
else
    echo "Please run the following command in a new terminal to launch the dashboard:"
    echo "streamlit run src/victory_bot/dashboard/streamlit_dashboard.py"
fi

# Tail the bot log for convenience
sleep 2
tail -n 40 -f live_bot.log
