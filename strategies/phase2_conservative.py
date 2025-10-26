import os, sys, time, subprocess

def run_one_cycle():
    # feed the interactive launcher automatically: A (Conservative), 8 hours
    answers = "YES I UNDERSTAND RISKS\nYES\nA\n8\nSTART LIVE TRADING\n"
    p = subprocess.Popen([sys.executable, "launch_live_trading.py"],
                         stdin=subprocess.PIPE, text=True)
    p.communicate(answers)
    return p.returncode

def main():
    run_forever = os.getenv("RUN_FOREVER","true").lower()=="true"
    sleep_s = int(os.getenv("SLEEP_BETWEEN_SCANS_SEC","30"))
    while True:
        rc = run_one_cycle()
        time.sleep(sleep_s)
        if not run_forever:
            break

if __name__ == "__main__":
    main()
