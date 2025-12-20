# CliniScribe - Super Easy Installation 🎉

## One-Time Setup (2 Steps!)

### Step 1: Install the App

**Download the DMG:**
```
Location: desktop-app/src-tauri/target/release/bundle/dmg/CliniScribe_1.0.0_aarch64.dmg
```

**Install:**
1. Double-click `CliniScribe_1.0.0_aarch64.dmg`
2. Drag CliniScribe to Applications folder
3. Eject the DMG

### Step 2: First Launch (Automatic Setup!)

**Launch CliniScribe** from Applications - Setup happens automatically!

The app will:
1. ✅ Detect this is first run
2. ✅ Show welcome screen with beautiful UI
3. ✅ **Automatically download AI models** (~5 GB, one-time)
4. ✅ Configure everything for you
5. ✅ Open to ready-to-use dashboard

**That's it!** No configuration needed - everything is automatic.

---

## What Makes This Easy?

### 🤖 Auto-Configuration Features

**Already Built-In:**

1. **Smart First-Run Detection**
   - App checks if setup is needed
   - Automatically shows setup wizard
   - No manual configuration required

2. **Automatic Model Downloads**
   - Whisper base model (~150 MB) - for transcription
   - Llama 3.1 8B (~4.7 GB) - for AI summaries
   - Progress bars show download status
   - One-time download, stored locally

3. **Self-Starting Services**
   - Ollama server starts automatically
   - Python API starts automatically
   - Health monitoring built-in
   - Green status indicators when ready

4. **Zero Config Recording**
   - Microphone access requested automatically
   - Browser handles device selection
   - No settings needed to start recording

5. **Smart Defaults**
   - Best model sizes pre-selected
   - Optimal summary length (15%)
   - Quality settings balanced for speed
   - Storage locations set automatically

---

## Installation Time Breakdown

| Step | Time | What Happens |
|------|------|--------------|
| **Install App** | 1 minute | Drag to Applications |
| **First Launch** | 5-15 minutes | Models download automatically |
| **Ready to Use** | Instant | Process lectures immediately! |

**Total: ~6-16 minutes** (mostly waiting for downloads)

---

## Using CliniScribe After Setup

### Option 1: Upload a Recording

1. Click **Upload** area
2. Select audio file (MP3, WAV, M4A, etc.)
3. Optional: Choose subject, summary length
4. Click **Process**
5. Wait 1-5 minutes
6. Get study notes + transcript!

### Option 2: Record Live (NEW!)

1. Click **Start Recording** in Record card
2. Allow microphone access (one-time)
3. Speak - see live preview of transcription!
4. Click **Stop** when done
5. Save recording (or discard)
6. Click **Process**
7. Get study notes + transcript!

---

## What You Get

### ✨ Study Notes
- Learning objectives
- Core concepts explained
- Clinical terms defined
- Key procedures summarized
- Formatted in Markdown

### 📝 Full Transcript
- Word-for-word transcription
- Timestamps for each segment
- Searchable text
- Copy/paste friendly

### 🎯 Quiz Questions
- Subject-based questions
- Or lecture-specific questions
- Multiple choice format
- Great for self-testing

### 💾 Export Options
- Save as Markdown (.md)
- Import to Notion, Obsidian, etc.
- Print-friendly format

---

## Live Recording Features

### 🎙️ Real-Time Capabilities

**Live Preview:**
- Rough transcription appears while speaking
- See text within ~5 seconds
- Helps verify microphone is working
- Preview updates every 5 seconds

**Recording Controls:**
- ⏺️ Start/Stop
- ⏸️ Pause/Resume
- Timer shows duration
- Visual recording indicator

**Final Processing:**
- High-quality transcription after stopping
- Uses full audio preprocessing
- More accurate than live preview
- Same pipeline as uploaded files

---

## System Requirements

✅ **Minimum:**
- macOS 10.15 or later
- 8 GB RAM
- 10 GB free storage
- Internet (for first-time setup)

⚡ **Recommended:**
- macOS 11.0 or later
- 16 GB RAM
- SSD storage
- Good internet (faster model downloads)

---

## Troubleshooting (Rare!)

### If Setup Wizard Doesn't Start

```bash
# Delete config to trigger first-run again
rm -rf ~/Library/Application\ Support/cliniscribe
# Relaunch CliniScribe
```

### If Models Don't Download

1. **Check Internet:** Ensure stable connection
2. **Check Space:** Need ~10 GB free
3. **Check Firewall:** Allow CliniScribe
4. **Restart:** Quit and relaunch app

### If Recording Doesn't Work

1. **Grant Permissions:**
   - System Settings → Privacy & Security → Microphone
   - Enable for CliniScribe

2. **Test Microphone:**
   - Check in System Settings → Sound → Input
   - Ensure microphone is detected

3. **Try Different Browser:**
   - Tauri uses system webview
   - Update macOS if needed

---

## Tips for Best Results

### 🎤 Recording Quality

✅ **Do:**
- Use external microphone
- Record from front of room
- Test before important lectures
- Keep under 2 hours

❌ **Avoid:**
- Built-in laptop mic (if possible)
- Recording from back of room
- Very noisy environments
- Recording through walls

### ⚡ Processing Speed

**Fast Mode (2-3 minutes per hour):**
- Use Whisper "base" model
- Brief summary length
- No GPU needed

**Quality Mode (5-10 minutes per hour):**
- Use Whisper "medium" model
- Standard/detailed summary
- Better accuracy

### 📚 Subject Selection

**Choose subject for better notes:**
- Anatomy → Emphasizes structures
- Physiology → Focuses on processes
- Pharmacology → Highlights drug info
- Clinical Skills → Procedure steps

**Leave blank for general:**
- Mixed topics
- Review sessions
- Study groups

---

## Pre-Configured Settings

**You don't need to change these** - but you can if you want!

| Setting | Default | Why |
|---------|---------|-----|
| Whisper Model | Base | Balance of speed/accuracy |
| Summary Length | 15% | Good detail without overwhelming |
| Auto-Delete | 7 days | Keep disk usage low |
| GPU | Off | Most Macs don't have NVIDIA |
| Recording Format | WAV | Best quality, no encoding |

**To change:** Click ⚙️ Settings in top-right

---

## What's Already Set Up?

✅ **Backend Services:**
- Ollama server (port 11436)
- Python API (port 8080)
- Auto-start on launch
- Health monitoring

✅ **AI Models:**
- Whisper: Speech-to-text
- Llama 3.1: Text generation
- Auto-downloaded on setup
- Cached locally

✅ **Storage:**
- Config: `~/Library/Application Support/cliniscribe`
- Models: `~/.cache/huggingface` + `~/.ollama`
- Audio: Configurable in settings

✅ **Security:**
- Everything runs locally
- No cloud uploads
- Your data stays private
- Microphone permissions controlled

---

## Quick Start Checklist

After installation:

- [ ] Launch CliniScribe
- [ ] Wait for setup wizard (automatic)
- [ ] See green status indicators in header
- [ ] Upload a test file OR record yourself
- [ ] Click "Process"
- [ ] View your first set of study notes!
- [ ] Export as Markdown
- [ ] Customize settings if desired

**Time to first study notes: ~20 minutes** (including setup)

---

## Where to Find Your Build

**Application:**
```
/Users/billp/Documents/GitHub/Cliniscribe/desktop-app/src-tauri/target/release/bundle/macos/CliniScribe.app
```

**DMG Installer:**
```
/Users/billp/Documents/GitHub/Cliniscribe/desktop-app/src-tauri/target/release/bundle/dmg/CliniScribe_1.0.0_aarch64.dmg
```

**To share:**
- Just send the DMG file
- Recipients double-click to install
- Everything auto-configures on first run!

---

## That's It!

**Three things you need to know:**

1. **Install:** Drag app to Applications
2. **Launch:** Setup happens automatically
3. **Use:** Upload or record lectures, get notes!

Everything else is automatic. Enjoy! 🎓✨
