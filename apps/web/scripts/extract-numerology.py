import sys
path = r"apps\web\src\components\numerology\MeenaNumerologyDashboard.tsx"
start = int(sys.argv[1])
end = int(sys.argv[2])
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
print("".join(lines[start:end]))
