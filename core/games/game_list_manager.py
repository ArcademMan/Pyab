import json
import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QMessageBox, QListWidgetItem, QDialog, QFileDialog

from core.database.game import GAME_LIST
from core.settings.settings import DEFAULT_BACKUP_PATH
from core.ui.pyab_game_list import Ui_GameList
from core.utils.path.path_assembler import PathBuilder
from core.shared.i18n import t
from core.utils.widgets.image_cache import ImageCache

logger = logging.getLogger(__name__)


def _apply_dark_titlebar(widget):
	try:
		import ctypes
		hwnd = int(widget.winId())
		dwmapi = ctypes.windll.dwmapi
		value = ctypes.c_int(1)
		result = dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
		if result != 0:
			dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value), ctypes.sizeof(value))
	except Exception:
		pass


class GameListManager(QDialog):
	def __init__(self, app):
		super().__init__(app)
		self.games = []
		self.filtered_games = []
		self.app = app
		self.ui = Ui_GameList()
		self.ui.setupUi(self)
		self.setWindowTitle(t("game_list_manager"))
		_apply_dark_titlebar(self)
		self.profile_path = PathBuilder.get_user_data_path("games.json")
		self._setup_connections()
		self.games = self.load_profiles()

	def _setup_connections(self):
		connections = [
			(self.ui.listWidget.currentRowChanged, self.show_game_details),
			(self.ui.game_list_filter.textChanged, self.filter_game_list),
			(self.ui.create_new_btn.clicked, self.create_new_game),
			(self.ui.dupe_selected_btn.clicked, self.duplicate_game),
			(self.ui.delete_selected_btn.clicked, self.delete_game),
			(self.ui.edit_selected_btn.clicked, self.edit_game),
			(self.ui.save_file_path_btn.clicked, self.open_save_file_path),
			(self.ui.backup_path_btn.clicked, self.open_backup_file_path)
		]
		for signal, slot in connections:
			signal.connect(slot)

	def load_profiles(self):
		try:
			if os.path.isfile(self.profile_path):
				with open(self.profile_path, "r", encoding="utf-8") as f:
					content = f.read().strip()
					return json.loads(content) if content else GAME_LIST
		except Exception as e:
			logger.error(f"Error loading profiles: {e}")
		return GAME_LIST

	def save_profiles(self):
		try:
			os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
			with open(self.profile_path, "w", encoding="utf-8") as f:
				json.dump(self.games, f, indent=4, ensure_ascii=False)
		except Exception as e:
			logger.error(f"Error saving profiles: {e}")

	def populate_game_list(self, games=None, select_name=None):
		self.ui.listWidget.clear()
		show_games = self.games if games is None else games

		for game in show_games:
			item = QListWidgetItem(game["name"])
			icon_path = PathBuilder.get_resource_path(f"icons/{game['icon']}")
			icon = ImageCache.get_scaled_icon(icon_path, width=24, height=24)  # usa cache e ridimensiona
			item.setIcon(icon)
			self.ui.listWidget.addItem(item)

		if select_name:
			self.select_game_by_name(select_name)

		self.filtered_games = show_games

	def filter_game_list(self, text):
		text = text.lower().strip()
		filtered = [g for g in self.games if text in g["name"].lower()] if text else self.games
		self.populate_game_list(filtered)
		if self.ui.listWidget.count() > 0:
			self.ui.listWidget.setCurrentRow(0)
		else:
			self.show_game_details(-1)

	def show_game_details(self, index):
		list_to_use = self.filtered_games if self.filtered_games else self.games
		fields = [
			self.ui.name,
			self.ui.file_name,
			self.ui.exe_name,
			self.ui.save_file_path,
			self.ui.backup_path,
			self.ui.note,
			self.ui.icon,
			self.ui.watch_line_edit,
		]

		if 0 <= index < len(list_to_use):
			game = list_to_use[index]
			values = [
				game.get("name", ""),
				game.get("save_name", ""),
				game.get("game_exe_name", ""),
				game.get("save_file_path", ""),
				game.get("backups_path", "") or DEFAULT_BACKUP_PATH,
				game.get("note", ""),
				game.get("icon", ""),
				game.get('watch_file', "")
			]
			for field, value in zip(fields, values):
				try:
					field.setText(value)
				except AttributeError:
					field.setPlainText(value)

			iconpath = PathBuilder.get_asset_path(f"icons/{game.get('icon', '')}.png")
			pm_small = ImageCache.get_scaled_pixmap(iconpath, 120, 120)
			if not pm_small.isNull():
				self.ui.game_icon.setPixmap(pm_small)
			else:
				self.ui.game_icon.clear()

		else:
			for field in fields:
				field.clear()

	def open_game_list(self, select_name=None):
		self.games = self.load_profiles()
		self.populate_game_list(select_name=select_name)
		return self.exec()

	def name_exists(self, name):
		return any(game["name"] == name for game in self.games)

	def _generate_unique_name(self, base_name, suffix=""):
		i = 1
		new_name = f"{base_name}{suffix} {i}" if suffix else f"{base_name} {i}"
		while self.name_exists(new_name):
			i += 1
			new_name = f"{base_name}{suffix} {i}" if suffix else f"{base_name} {i}"
		return new_name

	def _update_and_select(self, select_index=-1):
		self.save_profiles()
		self.populate_game_list(self.games)
		if select_index >= 0:
			self.ui.listWidget.setCurrentRow(select_index)

	def create_new_game(self):
		new_name = self._generate_unique_name("New Game")
		new_game = {
			"name": new_name,
			"save_name": "",
			"game_exe_name": "",
			"save_file_path": "",
			"backups_path": "",
			"icon": "",
			"watch_file": "",
		}
		self.games.append(new_game)
		self._update_and_select(len(self.games) - 1)
		return new_name

	def duplicate_game(self):
		index = self.ui.listWidget.currentRow()
		list_to_use = self.filtered_games if self.filtered_games else self.games

		if 0 <= index < len(list_to_use):
			original = list_to_use[index]
			clone = original.copy()
			clone["name"] = self._generate_unique_name(original["name"], " (cloned")
			self.games.append(clone)
			self._update_and_select(len(self.games) - 1)

	def delete_game(self):
		index = self.ui.listWidget.currentRow()
		list_to_use = self.filtered_games if self.filtered_games else self.games

		if 0 <= index < len(list_to_use):
			game_to_delete = list_to_use[index]
			game_name = game_to_delete['name']

			# Conta profili associati per informare l'utente
			profile_count = sum(
				1 for p in self.app.profile_manager.profiles
				if p.get("game_name") == game_name
			)
			msg = t("delete_game_confirm", name=game_name)
			if profile_count > 0:
				msg += "\n\n" + t("delete_game_cascade", count=profile_count)

			reply = QMessageBox.question(self, t("confirm_deletion"), msg,
			                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if reply == QMessageBox.Yes:
				self.games = [g for g in self.games if g["name"] != game_name]
				# Cascade delete: rimuovi profili associati
				self.app.profile_manager.profiles = [
					p for p in self.app.profile_manager.profiles
					if p.get("game_name") != game_name
				]
				self.app.profile_manager.save_profiles()
				self._update_and_select()
				self.show_game_details(-1)

	def _validate_game_fields(self):
		"""Valida i campi del gioco. Ritorna (ok, error_message)."""
		name = self.ui.name.text().strip()
		if not name:
			return False, t("validation.name_empty")

		save_name = self.ui.file_name.text().strip()
		if not save_name:
			return False, t("validation.save_name_empty")

		exe_name = self.ui.exe_name.text().strip()
		if not exe_name:
			return False, t("validation.exe_name_empty")

		save_path = self.ui.save_file_path.text().strip()
		if not save_path:
			return False, t("validation.save_path_empty")

		return True, ""

	def edit_game(self):
		index = self.ui.listWidget.currentRow()
		list_to_use = self.filtered_games if self.filtered_games else self.games

		if 0 <= index < len(list_to_use):
			game = list_to_use[index]

			# Validazione campi
			valid, error_msg = self._validate_game_fields()
			if not valid:
				QMessageBox.warning(self, t("validation.validation_error"), error_msg)
				return

			new_name = self.ui.name.text().strip()

			if new_name != game["name"] and self.name_exists(new_name):
				QMessageBox.warning(self, t("error"), t("name_exists", name=new_name))
				return

			# Update game data
			fields = [
				"name",
				"save_name",
				"game_exe_name",
				"save_file_path",
				"backups_path",
				"note",
				"icon",
				"watch_file"
			]
			values = [
				self.ui.name.text().strip(),
				self.ui.file_name.text().strip(),
				self.ui.exe_name.text().strip(),
				self.ui.save_file_path.text().strip(),
				self.ui.backup_path.text().strip(),
				self.ui.note.toPlainText().strip(),
				self.ui.icon.text().strip(),
				self.ui.watch_line_edit.text().strip()
			]

			for field, value in zip(fields, values):
				game[field] = value

			# Update in main list
			for i, g in enumerate(self.games):
				if g["name"] == list_to_use[index]["name"]:
					self.games[i] = game
					self._update_and_select(i)
					QMessageBox.information(self, t("success"), t("game_saved", name=new_name))
					break

	def _open_path_dialog(self, current_path, dialog_type="folder"):
		if dialog_type == "folder":
			return QFileDialog.getExistingDirectory(self, "Choose backup folder", current_path or "")
		else:
			start_dir = ""
			if current_path:
				start_dir = os.path.dirname(current_path) if os.path.isfile(current_path) else current_path
			return QFileDialog.getOpenFileName(self, "Choose save file", start_dir, "All files (*.*)")[0]

	def open_backup_file_path(self):
		index = self.ui.listWidget.currentRow()
		list_to_use = self.filtered_games if self.filtered_games else self.games

		if 0 <= index < len(list_to_use):
			directory = self._open_path_dialog(PathBuilder.resolve_path_template(self.ui.backup_path.text()), "folder")
			if directory:
				self.ui.backup_path.setText(directory)

	def open_save_file_path(self):
		index = self.ui.listWidget.currentRow()
		list_to_use = self.filtered_games if self.filtered_games else self.games

		if 0 <= index < len(list_to_use):
			file_path = self._open_path_dialog(PathBuilder.resolve_path_template(self.ui.save_file_path.text()), "folder")
			if file_path:
				self.ui.save_file_path.setText(file_path)

	def select_game_by_name(self, name):
		for index, game in enumerate(self.games):
			if game["name"] == name:
				self.ui.listWidget.setCurrentRow(index)
				self.show_game_details(index)
				return game

		return None
