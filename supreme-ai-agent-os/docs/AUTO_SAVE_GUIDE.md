# ⚙️ Auto-Save to Git - Complete Guide

Choose the auto-save method that works best for your workflow.

## 🎯 Quick Overview

| Method | Setup Time | Auto Frequency | Best For |
|--------|-----------|---|---|
| **Manual** | 0 min | On-demand | Explicit control |
| **Cron** | 2 min | Every 5 min (configurable) | Background automation |
| **Watch** | 5 min | Real-time (file changes) | Active development |
| **Git Hook** | 1 min | After each commit | Always connected |

---

## Option 1️⃣: Manual Auto-Commit (Simplest)

### Single commit + save
```bash
bash scripts/auto-commit.sh
```

### Commit + Push to GitHub
```bash
bash scripts/auto-commit.sh --push
```

**Output:**
```
✓ Auto-committed changes at 2024-06-03 19:45:30
✓ Pushed to remote
```

### When to use:
- Quick manual saves before important work
- When you want explicit control
- No background processes

---

## Option 2️⃣: Scheduled Auto-Commit (Every 5 minutes)

### Setup (one-time)
```bash
# Open crontab editor
crontab -e

# Add this line:
*/5 * * * * cd /workspaces/supreme-ai-agent-os && bash scripts/auto-commit.sh --push

# Save and exit (Ctrl+X, then Y)
```

### View your scheduled jobs
```bash
crontab -l
```

### Remove scheduled jobs
```bash
crontab -r
```

### Schedule examples
```bash
# Every 5 minutes
*/5 * * * * cd /path && bash scripts/auto-commit.sh --push

# Every 10 minutes
*/10 * * * * cd /path && bash scripts/auto-commit.sh --push

# Every hour
0 * * * * cd /path && bash scripts/auto-commit.sh --push

# Every hour during work hours (9-17)
0 9-17 * * 1-5 cd /path && bash scripts/auto-commit.sh --push

# Every 30 minutes
*/30 * * * * cd /path && bash scripts/auto-commit.sh --push
```

**When to use:**
- Background automation while you work
- Don't want to manage commits manually
- Need regular checkpoints

---

## Option 3️⃣: Real-Time Watch Mode (Active Development)

### Prerequisites
```bash
# Install inotify-tools (watches for file changes)
sudo apt-get install inotify-tools
```

### Start watching for changes
```bash
bash scripts/watch-and-commit.sh
```

**Output:**
```
👀 Watching for changes (Ctrl+C to stop)...
📁 Monitoring: /workspaces/supreme-ai-agent-os
📝 Change detected: frontend/streamlit/app.py
✓ Auto-committed changes at 2024-06-03 19:45:45
✓ Pushed to remote
```

### Stop watching
```
Press Ctrl+C
```

### Run in background (don't close terminal)
```bash
nohup bash scripts/watch-and-commit.sh &
```

**When to use:**
- Active development where you want every change saved
- Working on critical features
- Want automatic git history

---

## Option 4️⃣: Git Hook (Auto-Push After Commits)

### Already installed! ✅

The hook was created at `.git/hooks/post-commit` and automatically:
- Pushes to remote after every commit
- Works silently (no output)
- Handles errors gracefully

### How it works
```
You commit → Git hook runs → Automatic push to GitHub
```

### Manual commits with hook
```bash
git add .
git commit -m "your message"  # Automatically pushes!
```

### Or use our script
```bash
bash scripts/auto-commit.sh --push  # Commits, hook auto-pushes
```

**When to use:**
- Every commit should be pushed
- Always want GitHub in sync
- Minimal overhead

---

## 🔧 Advanced: Combine Methods

### Best practice workflow
```bash
# 1. Start watch mode in background
nohup bash scripts/watch-and-commit.sh &

# 2. Also add cron for safety (every 30 min)
crontab -e
# Add: */30 * * * * cd /workspaces/supreme-ai-agent-os && bash scripts/auto-commit.sh --push

# 3. Git hook handles auto-push
# (already installed)
```

This gives you:
- ✅ Real-time saves while you work
- ✅ Safety checkpoints every 30 min
- ✅ Automatic GitHub sync

---

## 📊 Monitoring Your Auto-Saves

### View recent commits
```bash
git log --oneline -10
# Shows your auto-commits with timestamps
```

### Check if watching is running
```bash
ps aux | grep watch-and-commit
```

### Kill watch process
```bash
pkill -f watch-and-commit.sh
```

### View cron logs
```bash
# macOS
log stream --predicate 'process == "cron"' --level debug

# Linux
sudo journalctl -u cron --follow
```

---

## 🚨 Troubleshooting

### "Not a git repository"
```bash
# Make sure you're in the project root
cd /workspaces/supreme-ai-agent-os
git status  # Should work
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x scripts/auto-commit.sh
chmod +x scripts/watch-and-commit.sh
```

### "inotifywait not found"
```bash
# Install inotify-tools
sudo apt-get install inotify-tools
```

### Nothing pushing to GitHub
```bash
# Check git remote
git remote -v
# Should show your GitHub repo

# Test push
git push origin main
```

### Cron not running
```bash
# Check cron service
sudo service cron status

# Restart if needed
sudo service cron restart
```

---

## 📝 Commit Message Format

All auto-commits use this format:
```
auto: update at 2024-06-03 19:45:30
```

This keeps your history clean while being searchable.

---

## 🎓 My Recommendation

### For Quick Work
```bash
bash scripts/auto-commit.sh --push  # Manual when done
```

### For Active Development
```bash
bash scripts/watch-and-commit.sh  # Real-time in background
```

### For Always-On
```bash
crontab -e
# Add: */15 * * * * cd /workspaces/supreme-ai-agent-os && bash scripts/auto-commit.sh --push
```

### For Production
Combine all three:
- Cron every 30 minutes
- Watch mode for active work
- Git hook for safety

---

## ✅ Status Check

See which auto-save methods are active:
```bash
echo "🔍 Checking auto-save status..."
echo ""
echo "Git Hook:"
[ -x .git/hooks/post-commit ] && echo "✅ Installed" || echo "❌ Not installed"
echo ""
echo "Cron jobs:"
crontab -l 2>/dev/null | grep supreme && echo "✅ Active" || echo "❌ None"
echo ""
echo "Watch process:"
ps aux | grep watch-and-commit | grep -v grep && echo "✅ Running" || echo "❌ Stopped"
```

---

**Choose your method and you'll never lose work again!** 🎉

