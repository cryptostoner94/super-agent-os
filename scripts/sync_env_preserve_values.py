from pathlib import Path

env_path = Path(".env")
example = Path(".env.example")
if not env_path.exists():
    env_path.write_text(example.read_text())

existing = {}
for line in env_path.read_text(errors="ignore").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, v = line.split("=", 1)
        existing[k.strip()] = v.strip()

out = []
for line in example.read_text().splitlines():
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        out.append(line)
        continue
    k, default = line.split("=", 1)
    out.append(f"{k}={existing.get(k, default)}")

extras = sorted(k for k in existing if not any(l.startswith(k + "=") for l in out))
if extras:
    out.append("")
    out.append("# ---- EXTRA KEYS PRESERVED FROM EXISTING .env ----")
    for k in extras:
        out.append(f"{k}={existing[k]}")
env_path.write_text("\n".join(out) + "\n")
print("Synced .env with .env.example while preserving existing values.")
