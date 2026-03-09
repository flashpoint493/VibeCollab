"""Mock host for demo_loop.yaml — echoes back each round."""
import sys

SENTINEL = "__VIBECOLLAB_EOM__"
round_num = 0

while True:
    lines = []
    for line in sys.stdin:
        line = line.rstrip("\n")
        if line == SENTINEL:
            break
        lines.append(line)
    if not lines:
        break
    round_num += 1
    print(f"Round {round_num}: Acknowledged. Following recommended next steps.")
    print(SENTINEL)
    sys.stdout.flush()
