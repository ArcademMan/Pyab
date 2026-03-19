<p align="center">
  <img src="Pyab.png" alt="PyAB Logo" width="128" height="128">
</p>

<h1 align="center">AmMstools - PyAB</h1>

<p align="center">
  <b>Game Save Backup Manager for Windows</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-beta-red" alt="Beta">
  <img src="https://img.shields.io/badge/platform-Windows-blue" alt="Windows">
  <img src="https://img.shields.io/badge/python-3.11+-yellow" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/UI-PySide6-green" alt="PySide6">
  <img src="https://img.shields.io/badge/license-MIT-gray" alt="MIT License">
</p>

---

PyAB automatically backs up your game save files so you never lose progress. It monitors save files in real time, captures screenshots, and lets you restore any backup with one click.

## Features

- **Automatic Backups** — timer-based or triggered by file changes (watchdog)
- **Game Detection** — pauses when the game isn't running, resumes when it is
- **Screenshot Capture** — saves a screenshot with each backup (auto-detects game monitor)
- **Multi-file Saves** — supports games with multiple save files (comma-separated)
- **Profile System** — multiple backup profiles per game with independent settings
- **Backup Management** — restore, delete, browse backups with context menu
- **Screenshot Preview** — click to zoom into full-size view
- **Backup Limits** — auto-cleanup by file count or total size
- **Path Templates** — flexible path resolution (`#Documents#`, `#Steam#`, `#AppData#`, `#ID#`)
- **Dark Theme** — Material Design-inspired dark UI
- **Localization** — English and Italian, switchable from Settings menu
- **Portable Data** — user data stored in `%APPDATA%/AmMstools/PyAB/`

## Installation

### Download (Recommended)

Download the latest installer from [Releases](https://github.com/ArcademMan/pyab/releases) and run `PyAB_Setup.exe`.

### From Source

```bash
git clone https://github.com/ArcademMan/pyab.git
cd pyab
pip install -r requirements.txt
python launcher.py
```

### Build Executable

```bash
pip install nuitka
python build.py
```

The standalone build will be in `launcher.dist/`.

### Create Installer

Requires [Inno Setup](https://jrsoftware.org/isinfo.php):

```bash
iscc installer.iss
```

## Path Templates

PyAB supports placeholders in save file paths for maximum flexibility:

| Placeholder | Resolves to |
|-------------|-------------|
| `#Documents#` | Documents folder (OneDrive-aware) |
| `#AppData#` | AppData root directory |
| `#Steam#` | Steam installation directory |
| `#Ubisoft#` | Ubisoft launcher directory |
| `#UserName#` | User profile directory |
| `#ID#` | First subdirectory (for Steam user IDs, etc.) |
| `#PYAB#` | Program base directory |

**Example:** `#Documents#\NBGI\DARK SOULS REMASTERED\#ID#`

## Project Structure

```
pyab/
├── launcher.py              # Entry point
├── core/
│   ├── pyab/                # Business logic (backup, file watcher)
│   ├── games/               # Game list manager
│   ├── profiles/            # Profile list manager
│   ├── ui/                  # PySide6 UI definitions
│   ├── shared/              # i18n, config, theme, validation
│   └── utils/               # Path resolver, image cache
├── assets/                  # Icons, locale files
├── build.py                 # Nuitka build script
└── installer.iss            # Inno Setup installer script
```

## Data Storage

| What | Where |
|------|-------|
| User data (games, profiles) | `%APPDATA%\AmMstools\PyAB\data\` |
| Settings (language) | `%APPDATA%\AmMstools\config.json` |
| Backups | Configurable per profile (default: next to exe) |

## Dependencies

- [PySide6](https://doc.qt.io/qtforpython-6/) — GUI framework
- [psutil](https://github.com/giampaolo/psutil) — Process monitoring
- [watchdog](https://github.com/gorakhargosh/watchdog) — File system events
- [mss](https://github.com/BoboTiG/python-mss) — Screenshot capture
- [Pillow](https://github.com/python-pillow/Pillow) — Image processing
- [pywin32](https://github.com/mhammond/pywin32) — Windows API

## Credits

Game cover images courtesy of [IGDB](https://www.igdb.com/) / Twitch Interactive, Inc.

## License

[MIT](LICENSE) — Code only. Game images are property of their respective owners. See [DISCLAIMER](DISCLAIMER.md).
