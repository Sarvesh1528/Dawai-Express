from datetime import datetime
import time

while True:
    now = datetime.now()
    min = now.minute
    sec = now.second
    time_str = now.strftime("%H:%M:%S")

    if min%2 == 0:
        if sec == 0:
            print(f"[{time_str}] → Morning Trigger")
        elif sec == 30:
            print(f"[{time_str}] → Afternoon Trigger")
    else:
        if sec == 0:
            print(f"[{time_str}] → Evening Trigger")
        elif sec == 30:
            print(f"[{time_str}] → Night Trigger")

    print(time_str)

    time.sleep(1)