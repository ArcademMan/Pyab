import base64

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices, QImage
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from core.database.glitch_icon import twitch_logo_base64
from core.games.game_list_manager import GameListManager
from core.profiles.profile_list_manager import ProfileListManager
from core.pyab.backup_manager import BackupManager
from core.settings.settings import DEFAULT_BACKUP_PATH
from core.ui.pyab import Ui_MainWindow
from core.utils.path.path_assembler import PathBuilder
from core.shared.i18n import t
from core.utils.widgets.image_cache import ImageCache


class Pyab:
	def __init__(self, app):
		self.app = app
		self.ui: Ui_MainWindow = app.ui
		self.game_manager: GameListManager = self.app.game_manager
		self.prof_manager: ProfileListManager = self.app.profile_manager
		self.games_path = PathBuilder.get_user_data_path("games.json")
		self.profile_path = PathBuilder.get_user_data_path("profiles.json")

		# Backup automatico
		self.backup_manager = BackupManager(self)

		# Variabili esistenti
		self.filtered_games = None
		self.filtered_profiles = None
		self.selected_game = None
		self.game_profiles = None
		self.selected_profile = None

		self.populate_game_list()
		self.setup_connections()
		self.apply_filters()
		self.load_favourite()

		data = base64.b64decode(twitch_logo_base64)
		image = QImage.fromData(data)
		pixmap = QPixmap.fromImage(image)
		pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		self.ui.twitch_logo.setPixmap(pixmap)


	def setup_connections(self):
		# GAMES
		self.ui.game_list_filter.textChanged.connect(self.filter_game_list)
		self.ui.create_game.clicked.connect(self.create_game)
		self.ui.edit_game.clicked.connect(self.edit_game)
		self.ui.selection_game_list.currentRowChanged.connect(self.select_game)

		# PROFILES
		self.ui.create_profile.clicked.connect(self.create_profile)
		self.ui.selection_profile_list.currentRowChanged.connect(self.select_profile)
		self.ui.edit_profile.clicked.connect(self.edit_profile)
		self.ui.launch_at_start_checkbox.stateChanged.connect(self.set_as_launch_start)
		self.ui.open_backup_path_btn.clicked.connect(self.open_backup_path)

		# NUOVE CHECKBOX PER I FILTRI
		self.ui.show_all_profiles.stateChanged.connect(self.apply_filters)
		self.ui.show_prof_game_only.stateChanged.connect(self.apply_filters)


	def apply_filters(self):
		self.update_game_list_with_filters()
		self.update_profile_list_with_filters()

	def update_game_list_with_filters(self):
		"""Aggiorna la lista dei giochi applicando i filtri"""
		all_games = self.get_games()

		# Se show_prof_game_only è attiva, mostra solo giochi con profili
		if self.ui.show_prof_game_only.isChecked():
			all_profiles = self.get_profiles()
			games_with_profiles = set(profile['game_name'] for profile in all_profiles)
			filtered_games = [game for game in all_games if game['name'] in games_with_profiles]
		else:
			filtered_games = all_games

		# Applica anche il filtro di testo se presente
		filter_text = self.ui.game_list_filter.text().lower().strip()
		if filter_text:
			filtered_games = [g for g in filtered_games if filter_text in g["name"].lower()]

		self.populate_game_list(filtered_games)

		# Se c'è almeno un gioco, seleziona il primo
		if self.ui.selection_game_list.count() > 0:
			self.ui.selection_game_list.setCurrentRow(0)

	def update_profile_list_with_filters(self):
		"""Aggiorna la lista dei profili applicando i filtri"""
		all_profiles = self.get_profiles()

		# Se show_all_profiles è attiva, mostra tutti i profili
		if self.ui.show_all_profiles.isChecked():
			filtered_profiles = all_profiles
		else:
			# Comportamento normale: mostra solo i profili del gioco selezionato
			if self.selected_game:
				filtered_profiles = [p for p in all_profiles if p.get("game_name") == self.selected_game["name"]]
			else:
				filtered_profiles = []

		self.populate_profiles_list(filtered_profiles)

	# ===== GAME LIST ========= (existing code with auto backup stop)
	def select_game(self, index):
		# Stop auto backup when changing game
		if self.backup_manager.auto_backup_active:
			self.backup_manager.stop_auto_backup()

		list_to_use = self.filtered_games if self.filtered_games else self.get_games()

		if 0 <= index < len(list_to_use):
			game = list_to_use[index]
			self.selected_game = game

			# Aggiorna la lista dei profili considerando i filtri
			self.update_profile_list_with_filters()
			self.reset_profiles_panel()
		else:
			self.selected_game = None
			self.game_profiles = None

	def select_profile(self, index):
		# Stop auto backup when changing profile
		if self.backup_manager.auto_backup_active:
			self.backup_manager.stop_auto_backup()

		if 0 <= index < len(self.filtered_profiles):
			profile = self.filtered_profiles[index]
			self.selected_profile = profile
			self.populate_profiles_section()
			self.backup_manager.refresh_backup_table()
		else:
			self.reset_profiles_panel()

	def filter_game_list(self, text):
		self.update_game_list_with_filters()

	def populate_game_list(self, games=None):
		self.ui.selection_game_list.clear()
		show_games = self.get_games() if games is None else games
		for game in show_games:
			item = QListWidgetItem(game["name"])
			icon_path = PathBuilder.get_resource_path(f"icons/{game['icon']}")
			icon = ImageCache.get_scaled_icon(icon_path, width=24, height=24)  # dimensione icona desiderata
			item.setIcon(icon)
			self.ui.selection_game_list.addItem(item)
		self.filtered_games = show_games

	def create_game(self):
		manager = self.game_manager
		name = manager.create_new_game()
		self.app.open_game_list_widget(select_name=name)

	def edit_game(self):
		if not self.selected_game:
			return
		name = self.selected_game['name']
		self.app.open_game_list_widget(select_name=name)

	# ======== PROFILES ===========

	def recalculate_profiles_list(self):
		self.ui.selection_profile_list.clear()
		if not self.selected_game:
			return
		game_profiles = [p for p in self.get_profiles() if p.get("game_name") == self.selected_game["name"]]
		self.populate_profiles_list(game_profiles)

	def reset_profiles_panel(self):
		self.selected_profile = None
		self.ui.backup_table.setRowCount(0)  # Pulisci anche la tabella dei backup

		self.ui.selected_profile.setText(t("profile_not_selected"))
		self.ui.save_file_found.setText("")
		self.ui.auto_backup_timer.setText("")
		self.ui.screenshots.setText("")
		self.ui.game_label.setText("")

		self.ui.launch_at_start_checkbox.blockSignals(True)
		self.ui.launch_at_start_checkbox.setChecked(False)
		self.ui.launch_at_start_checkbox.blockSignals(False)

		self.ui.game_icon.clear()

		self.ui.files_found.setText(f"")
		self.ui.weight_found.setText(f"")

	def create_profile(self):
		if not self.selected_game:
			QMessageBox.warning(self.app, t("no_game_selected"), t("select_game_first"))
			return
		manager = self.prof_manager
		profile_name = manager.create_new_profile(self.selected_game)
		self.app.open_profile_list_widget(game=self.selected_game, prof=profile_name)

	def edit_profile(self):
		if not self.selected_game:
			QMessageBox.warning(self.app, t("no_game_selected"), t("select_game_first"))
			return
		if not self.selected_profile:
			QMessageBox.warning(self.app, t("no_profile_selected"), t("select_profile_first"))
			return
		profile_name = self.selected_profile['profile_name']
		self.app.open_profile_list_widget(game=self.selected_game, prof=profile_name)

	def populate_profiles_list(self, profiles):
		self.ui.selection_profile_list.clear()
		show_profiles = profiles if profiles is not None else []
		for profile in show_profiles:
			item = QListWidgetItem(profile["profile_name"])
			if self.selected_game and "icon" in self.selected_game:
				icon_path = PathBuilder.get_resource_path(f"icons/{profile['icon']}")
				icon = ImageCache.get_scaled_icon(icon_path, width=24, height=24)  # usa cache e scala icona
				item.setIcon(icon)
			self.ui.selection_profile_list.addItem(item)
		self.filtered_profiles = show_profiles

	def set_as_launch_start(self, status):
		if status == 2:
			status = True
		else:
			status = False
		self.selected_profile['favourite'] = True
		profiles = self.get_profiles()
		for profile in profiles:
			if profile['profile_name'] == self.selected_profile['profile_name'] and profile['game_name'] == self.selected_profile['game_name']:
				profile['favourite'] = status
			else:
				profile['favourite'] = not status
		self.prof_manager.save_profiles()

	def populate_profiles_section(self):
		if not self.selected_profile:
			return

		profile = self.selected_profile
		self.ui.selected_profile.setText(profile['profile_name'])
		self.ui.save_file_found.setText(profile['save_name'])
		self.ui.auto_backup_timer.setText(f"{profile['auto_backup_timer']} sec")
		self.ui.screenshots.setText(str(profile['screenshot']))
		self.ui.game_label.setText(profile['game_name'])

		iconpath = PathBuilder.get_asset_path(f"icons/{profile.get('icon', '')}.png")
		self.ui.launch_at_start_checkbox.blockSignals(True)
		self.ui.launch_at_start_checkbox.setChecked(profile.get('favourite', False))
		self.ui.launch_at_start_checkbox.blockSignals(False)

		pm_small = ImageCache.get_scaled_pixmap(iconpath, width=160, height=160)
		if not pm_small.isNull():
			self.ui.game_icon.setPixmap(pm_small)
		else:
			self.ui.game_icon.clear()

		if profile['backups_path'] == DEFAULT_BACKUP_PATH:
			backup_path = PathBuilder.get_default_backup_path(profile['game_name'], profile['profile_name'])
		else:
			backup_path = profile['backups_path']

		# USA il metodo del BackupManager
		n_files, size = self.backup_manager.analyze_backup_folder(backup_path)
		self.ui.files_found.setText(f"{n_files}/{profile['max_backups_files']}")
		self.ui.weight_found.setText(f"{size}/{profile['max_size_files']} MB")

	def load_favourite(self):
		for profile in self.get_profiles():
			if profile.get('favourite', False):
				game_name = profile['game_name']

				# Seleziona il gioco nella lista visuale
				for i, game in enumerate(self.filtered_games or self.get_games()):
					if game['name'] == game_name:
						self.ui.selection_game_list.setCurrentRow(i)
						break

				# Seleziona il profilo nella lista visuale
				for i, p in enumerate(self.filtered_profiles or []):
					if p['profile_name'] == profile['profile_name']:
						self.ui.selection_profile_list.setCurrentRow(i)
						break
				return

	def open_backup_path(self):
		if not self.selected_profile:
			return False
		profile = self.selected_profile

		if profile['backups_path'] == DEFAULT_BACKUP_PATH:
			backup_path = PathBuilder.get_default_backup_path(profile['game_name'], profile['profile_name'])
		else:
			backup_path = profile['backups_path']

		# Costruiamo il path backup basandoci sulla cartella eseguibile per la backup dir accanto all'exe
		base_folder = PathBuilder.get_exe_folder()
		backup_folder = base_folder / backup_path

		backup_folder.mkdir(parents=True, exist_ok=True)
		QDesktopServices.openUrl(QUrl.fromLocalFile(str(backup_folder)))
		return True

	# ====== GENERAL =====

	def reload_after_edit(self):
		"""Ricarica liste dopo chiusura dialog di edit, mantenendo la selezione corrente."""
		saved_game = self.selected_game
		saved_profile = self.selected_profile

		# Ricarica dati aggiornati
		self.game_manager.games = self.game_manager.load_profiles()
		self.prof_manager.profiles = self.prof_manager.load_profiles()

		self.apply_filters()

		# Riseleziona gioco
		if saved_game:
			for i, g in enumerate(self.filtered_games or self.get_games()):
				if g['name'] == saved_game['name']:
					self.ui.selection_game_list.setCurrentRow(i)
					break

		# Riseleziona profilo
		if saved_profile:
			for i, p in enumerate(self.filtered_profiles or []):
				if p['profile_name'] == saved_profile['profile_name']:
					self.ui.selection_profile_list.setCurrentRow(i)
					break

	def get_games(self):
		return self.app.game_manager.games

	def get_profiles(self):
		return self.prof_manager.profiles
