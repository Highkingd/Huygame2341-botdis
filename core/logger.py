from datetime import datetime, timezone

def log(message: str):
    with open("log.txt", "a", encoding="utf-8") as f:
        t = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{t}] {message}\n")
