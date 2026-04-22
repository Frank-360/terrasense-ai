import datetime

with open("usage_log.txt", "a") as f:
    f.write(str(datetime.datetime.now()) + "\n")