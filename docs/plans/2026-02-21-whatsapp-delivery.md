# WhatsApp Delivery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a daily AI news briefing to WhatsApp as an MP3 voice note + bullet summary, triggered by GitHub Actions at 8 AM Dubai time.

**Architecture:** GitHub Actions cron job runs the existing Python pipeline (aggregate → script → TTS), then calls a Node.js script that uses whatsapp-web.js to send the MP3 as a voice note and a formatted bullet summary as a follow-up text message. WhatsApp session is pre-authenticated and stored as a base64 GitHub Secret.

**Tech Stack:** Python 3.11, Node.js 18, whatsapp-web.js, GitHub Actions, Anthropic API, OpenAI API

---

### Task 1: Add summary extraction to scriptwriter

The script writer currently returns only a plain text script. We need it to also return a structured list of stories (title + link) so we can generate the WhatsApp bullet summary.

**Files:**
- Modify: `src/scriptwriter.py`
- Modify: `src/main.py`
- Test: `tests/test_scriptwriter.py` (create)

**Step 1: Create tests directory and write failing test**

```bash
mkdir -p tests
touch tests/__init__.py
```

Create `tests/test_scriptwriter.py`:

```python
from src.scriptwriter import extract_story_list


def test_extract_story_list_returns_list():
    entries = [
        {"title": "GPT-5 Released", "link": "https://openai.com/gpt5", "source": "OpenAI Blog", "summary": "...", "published": "2026-02-21", "priority": "high"},
        {"title": "Claude 4 Launches", "link": "https://anthropic.com/claude4", "source": "Anthropic", "summary": "...", "published": "2026-02-21", "priority": "high"},
    ]
    result = extract_story_list(entries, max_stories=8)
    assert isinstance(result, list)
    assert len(result) <= 8
    assert all("title" in s and "link" in s and "source" in s for s in result)


def test_extract_story_list_respects_max():
    entries = [
        {"title": f"Story {i}", "link": f"https://example.com/{i}", "source": "Test", "summary": "...", "published": "2026-02-21", "priority": "medium"}
        for i in range(20)
    ]
    result = extract_story_list(entries, max_stories=5)
    assert len(result) <= 5
```

**Step 2: Run tests to verify they fail**

```bash
cd /Users/momalijaz/.omnara/worktrees/ai-news-caster/omnara/shrewdly-implosive
python -m pytest tests/test_scriptwriter.py -v
```

Expected: `ImportError: cannot import name 'extract_story_list'`

**Step 3: Implement `extract_story_list` in scriptwriter.py**

Add to the bottom of `src/scriptwriter.py`:

```python
def extract_story_list(entries: list[dict], max_stories: int = 8) -> list[dict]:
    """Return top N entries as a structured list for summary generation."""
    return [
        {"title": e["title"], "link": e["link"], "source": e["source"]}
        for e in entries[:max_stories]
    ]
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_scriptwriter.py -v
```

Expected: `2 passed`

**Step 5: Commit**

```bash
git add tests/__init__.py tests/test_scriptwriter.py src/scriptwriter.py
git commit -m "feat: add extract_story_list to scriptwriter"
```

---

### Task 2: Generate and save summary.json in main pipeline

`main.py` needs to save a `summary.json` alongside the archive so the Node.js sender can read it.

**Files:**
- Modify: `src/main.py`
- Test: `tests/test_main_summary.py` (create)

**Step 1: Write failing test**

Create `tests/test_main_summary.py`:

```python
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_summary_json_saved(tmp_path, monkeypatch):
    """summary.json must be written with title/link/source fields."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "audio").mkdir()
    (tmp_path / "archive").mkdir()

    fake_entries = [
        {"title": "Story A", "link": "https://a.com", "source": "SourceA",
         "summary": "...", "published": "2026-02-21", "priority": "high"},
    ]

    with patch("src.main.aggregate", return_value=fake_entries), \
         patch("src.main.write_script", return_value="This is the script."), \
         patch("src.main.generate_audio", return_value=str(tmp_path / "audio/briefing-2026-02-21.mp3")):
        from src.main import run
        run()

    summary_files = list(tmp_path.glob("archive/*-summary.json"))
    assert len(summary_files) == 1
    data = json.loads(summary_files[0].read_text())
    assert isinstance(data, list)
    assert data[0]["title"] == "Story A"
    assert data[0]["link"] == "https://a.com"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_main_summary.py -v
```

Expected: FAIL — no `*-summary.json` file found

**Step 3: Update `src/main.py` to save summary.json**

After the archive save block (around line 57), add:

```python
    # Save summary for WhatsApp delivery
    from src.scriptwriter import extract_story_list
    summary = extract_story_list(entries, max_stories=config_max_stories(config_path="config/config.yaml"))
    summary_path = f"archive/{today}-summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary saved: {summary_path}")
```

Also add a helper at the top of `main.py`:

```python
def config_max_stories(config_path: str = "config/config.yaml") -> int:
    import yaml
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("style", {}).get("max_stories", 8)
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_main_summary.py -v
```

Expected: `1 passed`

**Step 5: Commit**

```bash
git add src/main.py tests/test_main_summary.py
git commit -m "feat: save summary.json to archive for WhatsApp delivery"
```

---

### Task 3: Node.js WhatsApp sender script

A standalone Node.js script that reads the MP3 and summary.json, then sends both via whatsapp-web.js.

**Files:**
- Create: `scripts/package.json`
- Create: `scripts/send_whatsapp.js`

**Step 1: Create `scripts/package.json`**

```json
{
  "name": "whatsapp-sender",
  "version": "1.0.0",
  "description": "Send AI News Caster briefing via WhatsApp",
  "main": "send_whatsapp.js",
  "dependencies": {
    "whatsapp-web.js": "^1.23.0",
    "qrcode-terminal": "^0.12.0"
  }
}
```

**Step 2: Create `scripts/send_whatsapp.js`**

```javascript
/**
 * Send AI News Caster briefing via WhatsApp.
 *
 * Usage:
 *   node send_whatsapp.js <mp3_path> <summary_json_path> <target_number>
 *
 * Environment:
 *   WHATSAPP_SESSION - base64-encoded session JSON (optional, falls back to local .wwebjs_auth)
 *
 * target_number format: "971XXXXXXXXX" (country code, no +, no spaces)
 */

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const fs = require('fs');
const path = require('path');

const [,, mp3Path, summaryPath, targetNumber] = process.argv;

if (!mp3Path || !summaryPath || !targetNumber) {
  console.error('Usage: node send_whatsapp.js <mp3_path> <summary_json_path> <target_number>');
  process.exit(1);
}

// If WHATSAPP_SESSION env var is set, write it to disk for LocalAuth to pick up
const SESSION_DIR = path.join(__dirname, '.wwebjs_auth');
if (process.env.WHATSAPP_SESSION) {
  const sessionData = Buffer.from(process.env.WHATSAPP_SESSION, 'base64').toString('utf8');
  fs.mkdirSync(path.join(SESSION_DIR, 'session'), { recursive: true });
  fs.writeFileSync(path.join(SESSION_DIR, 'session', 'session.json'), sessionData);
  console.log('Session loaded from environment.');
}

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: SESSION_DIR }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  },
});

client.on('qr', (qr) => {
  // Only needed for first-time setup
  require('qrcode-terminal').generate(qr, { small: true });
  console.log('Scan the QR code above to authenticate WhatsApp.');
});

client.on('ready', async () => {
  console.log('WhatsApp client ready. Sending briefing...');

  const chatId = `${targetNumber}@c.us`;

  try {
    // 1. Send voice note (MP3)
    const mp3Data = fs.readFileSync(mp3Path);
    const mp3Base64 = mp3Data.toString('base64');
    const voiceMedia = new MessageMedia('audio/mpeg', mp3Base64, path.basename(mp3Path));
    await client.sendMessage(chatId, voiceMedia, { sendAudioAsVoice: true });
    console.log('Voice note sent.');

    // 2. Build and send text summary
    const stories = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));
    const today = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    let text = `*🎙️ AI News Briefing — ${today}*\n\n`;
    stories.forEach((story, i) => {
      text += `${i + 1}. *${story.title}*\n`;
      text += `   _${story.source}_ — ${story.link}\n\n`;
    });
    text += '_Daily briefing by AI News Caster_';

    await client.sendMessage(chatId, text);
    console.log('Text summary sent.');

  } catch (err) {
    console.error('Failed to send:', err);
    process.exit(1);
  }

  await client.destroy();
  process.exit(0);
});

client.on('auth_failure', (msg) => {
  console.error('Auth failure:', msg);
  process.exit(1);
});

client.initialize();
```

**Step 3: Install dependencies and do a local smoke test**

```bash
cd scripts
npm install
# Verify it at least loads without crashing (no actual send)
node -e "require('./send_whatsapp.js')" 2>&1 | head -5
cd ..
```

Expected: Usage error message (correct — no args passed)

**Step 4: Export your existing WhatsApp session to a base64 secret**

Your existing whatsapp-web.js session lives at `~/.wwebjs_auth/session/session.json` (or similar). Run:

```bash
# Find the session file
find ~ -name "session.json" -path "*wwebjs*" 2>/dev/null | head -3
```

Then encode it:

```bash
cat /path/to/session.json | base64 | tr -d '\n'
```

Copy that output — this is your `WHATSAPP_SESSION` GitHub Secret value.

**Step 5: Commit**

```bash
git add scripts/package.json scripts/send_whatsapp.js
git commit -m "feat: add WhatsApp sender script with voice note + summary"
```

---

### Task 4: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/daily-briefing.yml`

**Step 1: Create `.github/workflows/daily-briefing.yml`**

```bash
mkdir -p .github/workflows
```

```yaml
name: Daily AI News Briefing

on:
  schedule:
    - cron: '0 4 * * *'  # 4 AM UTC = 8 AM Dubai (UTC+4)
  workflow_dispatch:       # Allow manual trigger for testing

jobs:
  briefing:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        run: pip install -r requirements.txt

      - name: Run pipeline
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python -m src.main

      - name: Set up Node.js 18
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install Node dependencies
        run: npm install
        working-directory: scripts

      - name: Send WhatsApp briefing
        env:
          WHATSAPP_SESSION: ${{ secrets.WHATSAPP_SESSION }}
          WHATSAPP_TARGET_NUMBER: ${{ secrets.WHATSAPP_TARGET_NUMBER }}
        run: |
          TODAY=$(date +%Y-%m-%d)
          MP3="audio/briefing-${TODAY}.mp3"
          SUMMARY="archive/${TODAY}-summary.json"
          node scripts/send_whatsapp.js "$MP3" "$SUMMARY" "$WHATSAPP_TARGET_NUMBER"
```

**Step 2: Add GitHub Secrets**

Go to: `https://github.com/<your-repo>/settings/secrets/actions`

Add these 4 secrets:
| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `OPENAI_API_KEY` | Your OpenAI key |
| `WHATSAPP_SESSION` | base64 string from Task 3 Step 4 |
| `WHATSAPP_TARGET_NUMBER` | e.g. `971501234567` (no + or spaces) |

**Step 3: Push and trigger manually**

```bash
git add .github/workflows/daily-briefing.yml
git commit -m "feat: add GitHub Actions daily briefing workflow"
git push
```

Then go to GitHub → Actions → Daily AI News Briefing → Run workflow

**Step 4: Verify in GitHub Actions logs**

Expected output in logs:
```
=== AI News Caster - 2026-02-21 ===
[1/3] Aggregating news from RSS feeds...
[2/3] Writing briefing script...
[3/3] Generating audio...
WhatsApp client ready. Sending briefing...
Voice note sent.
Text summary sent.
```

---

### Task 5: Update .gitignore and requirements.txt

**Files:**
- Modify: `.gitignore`
- Modify: `requirements.txt`

**Step 1: Update `.gitignore`**

Add to `.gitignore`:

```
# WhatsApp session (never commit)
scripts/.wwebjs_auth/
scripts/node_modules/

# Generated outputs
scripts/*.mp3
```

**Step 2: Verify requirements.txt has all deps**

Current `requirements.txt` should contain:

```
anthropic
openai
feedparser
pyyaml
python-dotenv
```

Run:

```bash
pip install -r requirements.txt
python -c "import anthropic, openai, feedparser, yaml, dotenv; print('All deps OK')"
```

Expected: `All deps OK`

**Step 3: Commit**

```bash
git add .gitignore requirements.txt
git commit -m "chore: update gitignore and verify requirements"
```

---

## Done ✅

When all tasks are complete, the system will:
1. Run every day at 8 AM Dubai time via GitHub Actions
2. Generate a fresh AI news script + MP3
3. Send the MP3 as a WhatsApp voice note to your number
4. Follow up with a formatted bullet list of stories + links
