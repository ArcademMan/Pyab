import json
import logging
import os

from PySide6.QtWidgets import QMessageBox, QListWidgetItem, QDialog, QFileDialog

from core.settings.settings import DEFAULT_BACKUP_PATH
from core.ui.pyab_profile_list import Ui_ProfileList
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


class ProfileListManager(QDialog):
	def __init__(self, app):
		super().__init__(app)
		self.games = []
		self.profiles = []
		self.filtered_games = []
		self.filtered_profiles = []
		self.selected_game = None
		self.app = app
		self.ui = Ui_ProfileList()
		self.ui.setupUi(self)
		self.setWindowTitle(t("profile_list_manager"))
		_apply_dark_titlebar(self)
		self.profile_path = PathBuilder.get_user_data_path("profiles.json")
		self._setup_connections()
		self.profiles = self.load_profiles()

	def _setup_connections(self):
		connections = [
			# Connessioni corrette per le due liste separate
			(self.ui.game_list.currentRowChanged, self.on_game_selected),  # Quando seleziono un gioco
			(self.ui.profile_list.currentRowChanged, self.on_profile_selected),  # Quando seleziono un profilo
			(self.ui.game_list_filter.textChanged, self.filter_game_list),
			(self.ui.create_new_btn.clicked, self.create_new_profile),
			(self.ui.dupe_selected_btn.clicked, self.duplicate_profile),
			(self.ui.delete_selected_btn.clicked, self.delete_profile),
			(self.ui.edit_selected_btn.clicked, self.edit_profile),
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
					return json.loads(content) if content else []
		except Exception as e:
			logger.error(f"Error loading profiles: {e}")
		return []

	def save_profiles(self):
		try:
			os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
			with open(self.profile_path, "w", encoding="utf-8") as f:
				json.dump(self.profiles, f, indent=4, ensure_ascii=False)
		except Exception as e:
			logger.error(f"Error saving profiles: {e}")

	def populate_game_list(self, games=None, sgame=None, prof=None):
		"""Popola la lista dei giochi"""
		self.ui.game_list.clear()
		show_games = self.app.game_manager.games if games is None else games
		for game in show_games:
			item = QListWidgetItem(game["name"])
			icon_path = PathBuilder.get_resource_path(f"icons/{game['icon']}")
			icon = ImageCache.get_scaled_icon(icon_path, width=24, height=24)
			item.setIcon(icon)
			self.ui.game_list.addItem(item)

		self.filtered_games = show_games

		if sgame:
			self.selected_game = sgame
			self.select_game_by_name(sgame['name'])

		if prof:
			self.select_profile_by_name(prof)

	def populate_profile_list(self, profiles=None):
		"""Popola la lista dei profili per il gioco selezionato"""
		self.ui.profile_list.clear()
		show_profiles = profiles if profiles is not None else []

		for profile in show_profiles:
			item = QListWidgetItem(profile["profile_name"])
			# Usa l'icona del gioco associato se disponibile
			if self.selected_game and "icon" in self.selected_game:
				icon_path = PathBuilder.get_resource_path(f"icons/{self.selected_game['icon']}")
				icon = ImageCache.get_scaled_icon(icon_path, width=24, height=24)
				item.setIcon(icon)
			self.ui.profile_list.addItem(item)

		self.filtered_profiles = show_profiles

	def filter_game_list(self, text):
		"""Filtra la lista dei giochi"""
		text = text.lower().strip()
		filtered = [g for g in self.app.game_manager.games if text in g["name"].lower()] if text else self.app.game_manager.games
		self.populate_game_list(filtered)

		if self.ui.game_list.count() > 0:
			self.ui.game_list.setCurrentRow(0)
		else:
			self.on_game_selected(-1)

	def on_game_selected(self, index):

		if 0 <= index < len(self.filtered_games):
			self.selected_game = self.filtered_games[index]
			game_profiles = [p for p in self.profiles if p.get("game_name") == self.selected_game["name"]]
			self.populate_profile_list(game_profiles)
			self.clear_profile_fields()
		else:
			self.selected_game = None
			self.populate_profile_list([])
			self.clear_profile_fields()

	def on_profile_selected(self, index):
		"""Chiamato quando viene selezionato un profilo"""
		if 0 <= index < len(self.filtered_profiles):
			profile = self.filtered_profiles[index]
			self.show_profile_details(profile)
		else:
			self.clear_profile_fields()

	def show_profile_details(self, profile):
		"""Mostra i dettagli del profilo selezionato"""
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

		values = [
			profile.get("profile_name", ""),
			profile.get("save_name", ""),
			profile.get("game_exe_name", ""),
			profile.get("save_file_path", ""),
			profile.get("backups_path", "") or DEFAULT_BACKUP_PATH,
			profile.get("note", ""),
			profile.get("icon", ""),
			profile.get('watch_file') or ""
		]

		for field, value in zip(fields, values):
			try:
				field.setText(value)
			except AttributeError:
				field.setPlainText(value)

		self.ui.screenshot_cbox.setChecked(bool(profile.get('screenshot', False)))
		self.ui.max_backups_files.setValue(int(profile.get('max_backups_files', 100)))
		self.ui.max_size_files.setValue(int(profile.get('max_size_files', 1000)))
		self.ui.auto_backup_timer.setValue(int(profile.get('auto_backup_timer', 120)))

		if self.selected_game:
			iconpath = PathBuilder.get_asset_path(f"icons/{self.selected_game.get('icon', '')}.png")
			pm_small = ImageCache.get_scaled_pixmap(iconpath, 120, 120)
			if not pm_small.isNull():
				self.ui.game_icon.setPixmap(pm_small)
			else:
				self.ui.game_icon.clear()

	def clear_profile_fields(self):
		"""Pulisce tutti i campi del profilo"""
		fields = [
			self.ui.name, self.ui.file_name, self.ui.exe_name,
			self.ui.save_file_path, self.ui.backup_path, self.ui.note, self.ui.icon
		]

		for field in fields:
			try:
				field.clear()
			except (AttributeError, RuntimeError):
				pass

		self.ui.game_icon.clear()

	def open_profile_list(self, game, prof):
		"""Apre la finestra e inizializza le liste"""
		self.profiles = self.load_profiles()
		self.populate_game_list(sgame=game, prof=prof)
		return self.exec()

	def profile_name_exists(self, name, game_name):
		"""Controlla se esiste già un profilo con lo stesso nome per lo stesso gioco"""
		return any(p["profile_name"] == name and p.get("game_name") == game_name for p in self.profiles)

	def _generate_unique_profile_name(self, base_name, game_name):
		"""Genera un nome univoco per il profilo"""
		i = 1
		new_name = f"{base_name} {i}"
		while self.profile_name_exists(new_name, game_name):
			i += 1
			new_name = f"{base_name} {i}"
		return new_name

	def create_new_profile(self, selected_game=None):

		game_name = self.selected_game["name"] if not selected_game else selected_game['name']
		game = self.selected_game if not selected_game else selected_game
		if not game_name:
			QMessageBox.warning(self, t("error"), t("select_game_first"))
			return

		new_name = self._generate_unique_profile_name("New Profile", game_name)

		new_profile = {
			"profile_name": new_name,
			"game_name": game_name,
			"save_name": game["save_name"],
			"game_exe_name": game["game_exe_name"],
			"save_file_path": game["save_file_path"],
			"backups_path": game.get("backups_path", DEFAULT_BACKUP_PATH),
			"note": game.get('note', ""),
			"icon": game.get("icon", ""),
			"watch_file": game.get('watch_file', ""),
			"screenshot": True,
			"max_backups_files": 100,
			"max_size_files": 1000,
			"auto_backup_timer": 120,
		}

		self.profiles.append(new_profile)
		self.save_profiles()

		# Aggiorna la lista dei profili per il gioco corrente
		game_profiles = [p for p in self.profiles if p.get("game_name") == game_name]
		self.populate_profile_list(game_profiles)

		# Seleziona il nuovo profilo
		self.ui.profile_list.setCurrentRow(len(game_profiles) - 1)
		return new_name

	def duplicate_profile(self):
		"""Duplica il profilo selezionato"""
		index = self.ui.profile_list.currentRow()
		if 0 <= index < len(self.filtered_profiles):
			original = self.filtered_profiles[index]
			clone = original.copy()
			clone["profile_name"] = self._generate_unique_profile_name(original["profile_name"] + " (copy)", original["game_name"])

			self.profiles.append(clone)
			self.save_profiles()

			# Aggiorna la lista
			game_profiles = [p for p in self.profiles if p.get("game_name") == self.selected_game["name"]]
			self.populate_profile_list(game_profiles)
			self.ui.profile_list.setCurrentRow(len(game_profiles) - 1)

	def delete_profile(self):
		"""Elimina il profilo selezionato"""
		index = self.ui.profile_list.currentRow()
		if 0 <= index < len(self.filtered_profiles):
			profile_to_delete = self.filtered_profiles[index]

			reply = QMessageBox.question(self, t("confirm_deletion"),
			                             t("delete_profile_confirm", name=profile_to_delete['profile_name']),
			                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

			if reply == QMessageBox.Yes:
				self.profiles = [p for p in self.profiles if not (
						p["profile_name"] == profile_to_delete["profile_name"] and
						p.get("game_name") == profile_to_delete.get("game_name")
				)]
				self.save_profiles()

				# Aggiorna la lista
				if self.selected_game:
					game_profiles = [p for p in self.profiles if p.get("game_name") == self.selected_game["name"]]
					self.populate_profile_list(game_profiles)

				self.clear_profile_fields()

	def _validate_profile_fields(self):
		"""Valida i campi del profilo. Ritorna (ok, error_message)."""
		name = self.ui.name.text().strip()
		if not name:
			return False, t("validation.profile_name_empty")

		save_name = self.ui.file_name.text().strip()
		if not save_name:
			return False, t("validation.save_name_empty")

		exe_name = self.ui.exe_name.text().strip()
		if not exe_name:
			return False, t("validation.exe_name_empty")

		save_path = self.ui.save_file_path.text().strip()
		if not save_path:
			return False, t("validation.save_path_empty")

		max_files = self.ui.max_backups_files.value()
		if max_files < 1:
			return False, t("validation.max_files_invalid")

		max_size = self.ui.max_size_files.value()
		if max_size < 1:
			return False, t("validation.max_size_invalid")

		timer = self.ui.auto_backup_timer.value()
		if timer < 0:
			return False, t("validation.timer_invalid")

		return True, ""

	def edit_profile(self):
		"""Modifica il profilo selezionato"""
		index = self.ui.profile_list.currentRow()
		if 0 <= index < len(self.filtered_profiles):
			profile = self.filtered_profiles[index]

			# Validazione campi
			valid, error_msg = self._validate_profile_fields()
			if not valid:
				QMessageBox.warning(self, t("validation.validation_error"), error_msg)
				return

			new_name = self.ui.name.text().strip()
			game_name = profile.get("game_name", "")

			# Controlla se il nome è cambiato e se esiste già
			if new_name != profile["profile_name"] and self.profile_name_exists(new_name, game_name):
				QMessageBox.warning(self, t("error"), t("profile_exists", name=new_name))
				return

			# Aggiorna i dati del profilo
			fields = [
				"profile_name",
				"save_name",
				"game_exe_name",
				"save_file_path",
				"backups_path",
				"note",
				"icon",
				"watch_file",
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
				profile[field] = value

			profile["screenshot"] = self.ui.screenshot_cbox.isChecked()
			profile["max_backups_files"] = self.ui.max_backups_files.value()
			profile["max_size_files"] = self.ui.max_size_files.value()
			profile["auto_backup_timer"] = self.ui.auto_backup_timer.value()

			#   Aggiorna nella lista principale
			for i, p in enumerate(self.profiles):
				if (p["profile_name"] == self.filtered_profiles[index]["profile_name"] and
						p.get("game_name") == self.filtered_profiles[index].get("game_name")):
					self.profiles[i] = profile
					break

			self.save_profiles()

			# Aggiorna la visualizzazione
			game_profiles = [p for p in self.profiles if p.get("game_name") == self.selected_game["name"]]
			self.populate_profile_list(game_profiles)
			self.ui.profile_list.setCurrentRow(index)

			QMessageBox.information(self, t("success"), t("profile_saved", name=new_name))

	def _open_path_dialog(self, current_path, dialog_type="folder"):
		if dialog_type == "folder":
			return QFileDialog.getExistingDirectory(self, "Choose backup folder", current_path or "")
		else:
			start_dir = ""
			if current_path:
				start_dir = os.path.dirname(current_path) if os.path.isfile(current_path) else current_path
			return QFileDialog.getOpenFileName(self, "Choose save file", start_dir, "All files (*.*)")[0]

	def open_backup_file_path(self):
		index = self.ui.profile_list.currentRow()
		if 0 <= index < len(self.filtered_profiles):
			directory = self._open_path_dialog(PathBuilder.resolve_path_template(self.ui.backup_path.text()), "folder")
			if directory:
				self.ui.backup_path.setText(directory)

	def open_save_file_path(self):
		index = self.ui.profile_list.currentRow()
		if 0 <= index < len(self.filtered_profiles):
			file_path = self._open_path_dialog(PathBuilder.resolve_path_template(self.ui.save_file_path.text()), "folder")
			if file_path:
				self.ui.save_file_path.setText(file_path)

	def select_game_by_name(self, name):
		for index, game in enumerate(self.app.game_manager.games):
			if game["name"] == name:
				self.ui.game_list.setCurrentRow(index)
				self.on_game_selected(index)
				return game
		return None

	def select_profile_by_name(self, name):
		for index, profile in enumerate(self.filtered_profiles):
			if profile["profile_name"] == name:
				self.ui.profile_list.setCurrentRow(index)
				self.on_profile_selected(index)
				return profile
		return None
