import os, sys
import re

def parse(line):
    grps = re.findall(r"\[(.*?)\]", line)
    if not grps or len(grps) < 3 or grps[2] != "UDP":
        return None, None, None
    ip = grps[0]
    ts = grps[1]
    error = "ERROR" in line
    return ip, error, ts

def main():
    logs = sys.argv[1]

    with open(logs, 'r') as file:
        lines = file.readlines()

    #Key: IP Val: {error: <true/false>, ts: <timestamp>}
    last_log = {}

    for line in lines:
        ip, error, ts = parse(line.strip())
        if not ip:
            continue

        if ip in last_log:
            if ts < last_log[ip]["ts"]:
                continue
        last_log[ip] = { "error": error, "ts": ts}

    import pprint
    pprint.pprint(last_log)

    #Check no UDP errors
    for key, val in last_log.items():
        if val["error"] == True:
            print(f"FAILED: {key} -> {val})")
            sys.exit(1)

if __name__ == "__main__":
    main()
