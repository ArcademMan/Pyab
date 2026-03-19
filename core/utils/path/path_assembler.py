import os
import sys
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Optional, Literal
import winreg

class PathBuilder:
    """
    A utility class for resolving Windows path templates with various placeholders.

    Supported placeholders:
    - #AppData# => AppData root directory (not Roaming)
    - #Documents# => Documents folder (OneDrive or local)
    - #UserName# => User profile directory
    - #PYAB# => Program base directory
    - #GAME_NAME# => Game name parameter
    - #PROFILE_NAME# => Profile name parameter
    - #ID# => First subdirectory found (or based on strategy)
    """

    # Define the SelectStrategy type
    SelectStrategy = Literal["first", "alphabetical", "latest_modified"]

    @classmethod
    def get_exe_folder(cls):
        # Nuitka: usa __compiled__ invece di sys.frozen
        if "__compiled__" in globals():
            # Quando è compilato con Nuitka prendi la cartella dell'eseguibile finale
            return Path(sys.executable).resolve().parent
        else:
            # In esecuzione normale prendi la cartella corrente
            return Path.cwd().resolve()

    @classmethod
    def _get_steam_root(cls) -> str:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                val, _ = winreg.QueryValueEx(key, "SteamPath")
                return val
        except Exception:
            # fallback comune
            prog = os.environ.get("ProgramFiles(x86)") or "C:\\Program Files (x86)"
            return str(PureWindowsPath(prog) / "Steam")

    @classmethod
    def _get_ubisoft_root(cls) -> str:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Ubisoft\Launcher") as key:
                val, _ = winreg.QueryValueEx(key, "InstallDir")
                return str(PureWindowsPath(val))
        except Exception:
            prog = os.environ.get("ProgramFiles(x86)") or "C:\\Program Files (x86)"
            return str(PureWindowsPath(prog) / "Ubisoft" / "Ubisoft Game Launcher")

    @classmethod
    def _get_appdata_root(cls) -> str:
        """Get the AppData root directory (parent of Roaming)."""
        roaming = os.environ.get("APPDATA")
        if roaming:
            p = PureWindowsPath(roaming)
            # se finisce in Roaming, torna alla root AppData
            if p.name.lower() == "roaming":
                return str(p.parent)
            return str(p)
        # fallback generico
        return str(PureWindowsPath(os.path.expanduser("~")) / "AppData")

    @classmethod
    def _get_userprofile(cls) -> str:
        """Get the user profile directory."""
        up = os.environ.get("USERPROFILE")
        if up:
            return up
        return str(PureWindowsPath(os.path.expanduser("~")))

    @classmethod
    def _get_documents(cls) -> str:
        """
        Get the Documents directory, trying in order:
        - OneDrive\Documents
        - OneDrive\Documenti (localized)
        - %USERPROFILE%\Documents
        - %USERPROFILE%\Documenti
        """
        user = PureWindowsPath(cls._get_userprofile())
        one = os.environ.get("OneDrive")
        candidates = []
        if one:
            one = PureWindowsPath(one)
            candidates += [one / "Documents", one / "Documenti"]
        candidates += [user / "Documents", user / "Documenti"]
        for c in candidates:
            try:
                if Path(str(c)).exists():
                    return str(c)
            except Exception:
                pass
        # fallback
        return str(user / "Documents")

    @classmethod
    def _pick_id_subfolder(cls, base_dir: PureWindowsPath, strategy: SelectStrategy = "first"):
        p = Path(str(base_dir))
        if not p.is_dir():
            return None
        entries = [e for e in p.iterdir() if e.is_dir()]
        if not entries:
            return None
        if strategy in ("first", "alphabetical"):
            entries.sort(key=lambda x: x.name.lower())
        elif strategy == "latest_modified":
            entries.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return entries[0].name

    @classmethod
    def resolve_path_template(cls, path_template: str, game_name: Optional[str] = None, profile_name=None, id_strategy="first"):
        replacements = {
            "#appdata#": cls._get_appdata_root(),
            "#documents#": cls._get_documents(),
            "#username#": cls._get_userprofile(),
            "#pyab#": cls._get_program_base_dir(),
            "#game_name#": game_name or "",
            "#profile_name#": profile_name or "",
            "#steam#": cls._get_steam_root(),
            "#ubisoft#": cls._get_ubisoft_root(),
        }

        tmp = path_template
        for k, v in replacements.items():
            # Case-insensitive replace
            idx = tmp.lower().find(k)
            while idx != -1:
                tmp = tmp[:idx] + v + tmp[idx + len(k):]
                idx = tmp.lower().find(k, idx + len(v))
        pwin = PureWindowsPath(tmp)
        anchor = pwin.anchor
        built = PureWindowsPath(anchor) if anchor else PureWindowsPath()
        start_idx = 1 if anchor else 0
        for part in pwin.parts[start_idx:]:
            if part.lower() == "#id#":
                chosen = cls._pick_id_subfolder(built, strategy=id_strategy)
                built = built / (chosen if chosen else "ID_NOT_FOUND")
            elif part:
                built = built / part
        return str(built)

    @classmethod
    def _find_assets_root(cls) -> Path:
        # Nuitka: usa __compiled__ invece di sys.frozen e non ha sys._MEIPASS
        if "__compiled__" in globals():
            # Per Nuitka compilato, gli asset sono generalmente nella stessa directory dell'exe
            # o in una sottodirectory assets accanto all'exe
            exe_dir = Path(sys.executable).parent
            assets_path = exe_dir / "assets"
            if assets_path.exists() and assets_path.is_dir():
                return assets_path
            # Se non c'è la cartella assets, usa la directory dell'exe come base
            return exe_dir

        here = Path(__file__).resolve()
        for p in [here] + list(here.parents):
            cand = p / "assets"
            if cand.exists() and cand.is_dir():
                return cand
        cwd = Path.cwd().resolve()
        for p in [cwd] + list(cwd.parents):
            cand = p / "assets"
            if cand.exists() and cand.is_dir():
                return cand
        return Path(cls._get_program_base_dir()) / "assets"

    @classmethod
    def get_default_backup_path(cls, game_name: str, profile_name: str):
        template = r"#PYAB#\backups\#GAME_NAME#\#PROFILE_NAME#\Backups"
        return cls.resolve_path_template(template, game_name=game_name, profile_name=profile_name)

    @classmethod
    def get_resource_path(cls, relative_path: str) -> str:
        has_ext = any(relative_path.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".ico"))
        rel = relative_path if has_ext else (relative_path + ".png")
        base_path = cls._find_assets_root()
        full = (base_path / rel).resolve(strict=False)
        return str(full)

    @staticmethod
    def _resource_path(relative_path):
        # Aggiornato per Nuitka - non usa sys._MEIPASS
        if "__compiled__" in globals():
            # Per Nuitka: usa la directory dell'eseguibile come base
            base_path = str(Path(sys.executable).parent)
        else:
            # Development path
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    @staticmethod
    def get_asset_path(asset_name):
        return PathBuilder._resource_path(os.path.join("assets", asset_name))

    @staticmethod
    def get_user_data_path(filename=""):
        """Ritorna il path per i dati utente in %APPDATA%/AmMstools/PyAB/data/."""
        appdata = os.environ.get("APPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Roaming"))
        data_dir = os.path.join(appdata, "AmMstools", "PyAB", "data")
        os.makedirs(data_dir, exist_ok=True)
        if filename:
            return os.path.join(data_dir, filename)
        return data_dir

    @classmethod
    def _get_program_base_dir(cls) -> str:
        # Nuitka: usa __compiled__ invece di sys.frozen
        if "__compiled__" in globals():
            # App compilata con Nuitka
            exe_path = Path(sys.executable)
            launched_path = Path(sys.argv[0]) if sys.argv and sys.argv[0] else exe_path
            tempdir = Path(tempfile.gettempdir()).resolve()

            # Preferisci il percorso NON nel temp (quello lanciato dall'utente)
            candidates = [launched_path.resolve(), exe_path.resolve()]
            for p in candidates:
                try:
                    if p.exists() and tempdir not in p.parents:
                        return str(p.parent)
                except Exception:
                    pass
            # Fallback: dir dell'eseguibile
            return str(exe_path.parent)

        # Non compilato: prova dal main, poi CWD
        main = sys.modules.get("__main__")
        if main and getattr(main, "__file__", None):
            return str(Path(main.__file__).resolve().parent)
        return str(Path.cwd())
