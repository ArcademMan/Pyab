import base64
import ctypes
import logging
import sys

# DPI awareness — deve essere impostato PRIMA di creare QApplication
# altrimenti ImageGrab.grab() restituisce screenshot neri su monitor secondari
try:
	ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
	try:
		ctypes.windll.user32.SetProcessDPIAware()
	except Exception:
		pass

from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtGui import QIcon, QImage, QPixmap, QAction, QActionGroup
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox

from core.database.pyab_icon import PYAB_ICON
from core.games.game_list_manager import GameListManager
from core.profiles.profile_list_manager import ProfileListManager
from core.pyab.pyab_manager import Pyab
from core.settings.settings import APPVERSION
from core.shared.config import get as config_get, set as config_set
from core.shared.i18n import t, set_locale, get_locale, available_locales
from core.shared.theme import _BASE_STYLE
from core.ui.pyab import Ui_MainWindow

_LANGUAGE_LABELS = {
	"en": "English",
	"it": "Italiano",
}


class ModernMainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.setWindowTitle("AmMstools - Pyab")

		data = base64.b64decode(PYAB_ICON)
		image = QImage.fromData(data)
		pixmap = QPixmap.fromImage(image)
		icon = QIcon(pixmap)
		self.setWindowIcon(icon)

		self.setup_dark_theme()
		self._apply_dark_titlebar()
		self.increase_all_fonts(3)
		self.center_window()

		self.game_manager = GameListManager(self)
		self.profile_manager = ProfileListManager(self)
		self.pyab = Pyab(self)

		self._setup_language_menu()
		self._apply_translations()
		self.restore_settings()
		self.setup_connections()

	def setup_connections(self):
		self.ui.actionEdit_List.triggered.connect(self.open_game_list_widget)
		self.ui.actionShow_All_Profiles.triggered.connect(self.open_profile_list_widget)

	def _setup_language_menu(self):
		"""Aggiunge il menu Settings > Language alla menu bar."""
		self.menuSettings = QMenu(t("menu.settings"), self.ui.menuBar)
		self.menuSettings.setObjectName("menuSettings")

		self.menuLanguage = QMenu(t("menu.language"), self.menuSettings)
		self.menuLanguage.setObjectName("menuLanguage")

		lang_group = QActionGroup(self)
		lang_group.setExclusive(True)
		current_lang = get_locale()

		for lang_code in available_locales():
			label = _LANGUAGE_LABELS.get(lang_code, lang_code.upper())
			action = QAction(label, self)
			action.setCheckable(True)
			action.setChecked(lang_code == current_lang)
			action.setData(lang_code)
			action.triggered.connect(lambda checked, code=lang_code: self._on_language_changed(code))
			lang_group.addAction(action)
			self.menuLanguage.addAction(action)

		self.menuSettings.addMenu(self.menuLanguage)
		self.ui.menuBar.addAction(self.menuSettings.menuAction())

	def _on_language_changed(self, lang_code):
		"""Salva la lingua scelta e avvisa l'utente di riavviare."""
		config_set("language", lang_code)
		set_locale(lang_code)
		self._apply_translations()
		# Aggiorna anche i titoli del menu lingua
		self.menuSettings.setTitle(t("menu.settings"))
		self.menuLanguage.setTitle(t("menu.language"))

	def _apply_translations(self):
		"""Applica le traduzioni a tutti gli elementi UI."""
		# Menu bar
		self.ui.menuGames_List.setTitle(t("menu.games"))
		self.ui.menuProfiles.setTitle(t("menu.profiles"))
		self.ui.actionEdit_List.setText(t("menu.edit_list"))
		self.ui.actionAdd_New_Game.setText(t("menu.add_new_game"))
		self.ui.actionShow_All_Profiles.setText(t("menu.show_all_profiles"))

		# Sidebar - Games
		self.ui.label.setText(t("ui.games"))
		self.ui.show_prof_game_only.setText(t("ui.with_profiles"))
		self.ui.game_list_filter.setPlaceholderText(t("ui.search_game"))
		self.ui.create_game.setText(t("ui.create_game"))
		self.ui.edit_game.setText(t("ui.edit_game"))

		# Sidebar - Profiles
		self.ui.profiles_label.setText(t("ui.profiles"))
		self.ui.show_all_profiles.setText(t("ui.all_profiles"))
		self.ui.profile_list_filter.setPlaceholderText(t("ui.search_profile"))
		self.ui.create_profile.setText(t("ui.create_profile"))
		self.ui.edit_profile.setText(t("ui.edit_profile"))

		# Actions
		self.ui.launch_at_start_checkbox.setText(t("ui.launch_at_start"))
		self.ui.open_backup_path_btn.setText(t("ui.open_backup_path"))
		self.ui.delete_selected_backup.setText(t("ui.delete_selected"))
		self.ui.delete_all_backup.setText(t("ui.delete_all_backups"))

		# Game status
		self.ui.auto_backup_btn.setText(t("ui.toggle_auto_backup"))
		self.ui.backup_now_btn.setText(t("ui.backup_now"))
		self.ui.restore_backup_btn.setText(t("ui.restore_selected"))

		# Table headers
		self.pyab.backup_manager.setup_backup_table()

	def setup_dark_theme(self):
		self.setStyleSheet(_BASE_STYLE)

	def _apply_dark_titlebar(self):
		try:
			import ctypes
			hwnd = int(self.winId())
			dwmapi = ctypes.windll.dwmapi
			value = ctypes.c_int(1)
			result = dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
			if result != 0:
				dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value), ctypes.sizeof(value))
		except Exception:
			pass

	def increase_all_fonts(self, point_increase=3):
		app = QApplication.instance()
		current_font = app.font()
		new_size = current_font.pointSize() + point_increase
		current_font.setPointSize(new_size)
		app.setFont(current_font)

	def center_window(self):
		screen = QApplication.primaryScreen()
		if screen:
			screen_geometry = screen.availableGeometry()
			window_geometry = self.frameGeometry()
			window_geometry.moveCenter(screen_geometry.center())
			self.move(window_geometry.topLeft())

	def restore_settings(self):
		settings = QSettings("ArcademMan", "PyAB")
		self.restoreGeometry(settings.value("geometry", QByteArray()))
		self.restoreState(settings.value("windowState", QByteArray()))

	def closeEvent(self, event):
		if self.pyab.backup_manager.auto_backup_active:
			reply = QMessageBox.question(
				self, t("ui.auto_backup_active"),
				t("ui.auto_backup_quit_confirm"),
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No
			)
			if reply != QMessageBox.Yes:
				event.ignore()
				return
			self.pyab.backup_manager.stop_auto_backup()

		settings = QSettings("ArcademMan", "PyAB")
		settings.setValue("geometry", self.saveGeometry())
		settings.setValue("windowState", self.saveState())
		super().closeEvent(event)

	# =================== PROGRAM FUNCTIONS =====================

	def open_game_list_widget(self, select_name=None):
		self.game_manager.open_game_list(select_name)
		self.pyab.reload_after_edit()

	def open_profile_list_widget(self, game=None, prof=None):
		self.profile_manager.open_profile_list(game, prof)
		self.pyab.reload_after_edit()



def main():
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)

	# Inizializza la lingua prima di creare la UI
	saved_lang = config_get("language")
	if saved_lang:
		set_locale(saved_lang)
	else:
		get_locale()  # auto-detect dalla lingua di sistema

	app = QApplication(sys.argv)
	window = ModernMainWindow()
	window.show()

	sys.exit(app.exec())


if __name__ == "__main__":
	main()
