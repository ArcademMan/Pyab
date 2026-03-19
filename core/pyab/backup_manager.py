import datetime
import logging
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import mss
import mss.tools
import psutil
import win32gui
import win32process
from PySide6.QtCore import QObject, QPoint, QUrl
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QDesktopServices, QAction
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView, QAbstractItemView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox, QMenu
from watchdog.observers import Observer

from core.pyab.backup_performer import perform_backup
from core.pyab.file_watcher import FileWatcher
from core.settings.settings import DEFAULT_BACKUP_PATH
from core.shared.i18n import t
from core.utils.path.path_assembler import PathBuilder

logger = logging.getLogger(__name__)


def _find_game_monitor_index(exe_name):
	"""Trova l'indice del monitor mss su cui si trova la finestra del gioco.
	Ritorna l'indice 1-based per mss (0 = tutti i monitor, 1 = primo, 2 = secondo, ecc.)
	"""
	if not exe_name:
		return 0

	target_pids = set()
	for proc in psutil.process_iter(['pid', 'name']):
		if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
			target_pids.add(proc.info['pid'])

	if not target_pids:
		return 0

	best_hwnd = None
	best_area = 0

	def enum_callback(hwnd, _):
		nonlocal best_hwnd, best_area
		if not win32gui.IsWindowVisible(hwnd):
			return True
		try:
			_, pid = win32process.GetWindowThreadProcessId(hwnd)
			if pid in target_pids:
				rect = win32gui.GetWindowRect(hwnd)
				area = (rect[2] - rect[0]) * (rect[3] - rect[1])
				if area > best_area:
					best_area = area
					best_hwnd = hwnd
		except Exception:
			pass
		return True

	win32gui.EnumWindows(enum_callback, None)

	if not best_hwnd:
		return 0

	# Trova il centro della finestra del gioco
	rect = win32gui.GetWindowRect(best_hwnd)
	cx = (rect[0] + rect[2]) // 2
	cy = (rect[1] + rect[3]) // 2

	# Confronta con i monitor di mss per trovare quello giusto
	with mss.mss() as sct:
		for i, mon in enumerate(sct.monitors):
			if i == 0:
				continue  # indice 0 = tutti i monitor combinati
			if (mon["left"] <= cx < mon["left"] + mon["width"] and
					mon["top"] <= cy < mon["top"] + mon["height"]):
				return i

	return 1  # fallback al monitor primario


class BackupManager(QObject):
	file_modified_signal = Signal()

	def __init__(self, pyab_instance):
		super().__init__()
		self.pyab = pyab_instance
		self.app = pyab_instance.app
		self.ui = pyab_instance.ui

		self.file_modified_signal.connect(self._handle_file_modification)

		# Timer per backup automatico
		self.auto_backup_timer = QTimer()
		self.countdown_timer = QTimer()
		self.game_status_timer = None  # AGGIUNGI questo
		self.auto_backup_active = False
		self.file_observer = None
		self.backup_worker = None
		self.remaining_seconds = 0

		# Cache per analyze_backup_folder
		self._analysis_cache = {}  # {backup_path: (n_files, size_mb, timestamp)}

		# Screenshot corrente per popup zoom
		self._current_screenshot_pixmap = None

		self._setup_connections()
		self.setup_backup_table()

	def _setup_connections(self):
		"""Configura le connessioni per i controlli di backup"""
		self.ui.auto_backup_btn.clicked.connect(self.toggle_auto_backup)
		self.auto_backup_timer.timeout.connect(self.check_and_backup)
		self.countdown_timer.timeout.connect(self.update_countdown)
		self.ui.backup_table.itemSelectionChanged.connect(self.on_backup_row_selected)

		# Nuove connessioni per i pulsanti
		self.ui.delete_selected_backup.clicked.connect(self.delete_selected_backup)
		self.ui.delete_all_backup.clicked.connect(self.delete_all_backups)
		self.ui.restore_backup_btn.clicked.connect(self.restore_selected_backup)
		self.ui.backup_now_btn.clicked.connect(self.backup_now)

		self.ui.backup_table.setContextMenuPolicy(Qt.CustomContextMenu)
		self.ui.backup_table.customContextMenuRequested.connect(self.show_backup_context_menu)

		self.ui.graphicsView.mousePressEvent = self._on_screenshot_clicked

	def setup_backup_table(self):
		"""Configura la tabella dei backup"""
		self.ui.backup_table.setColumnCount(3)
		self.ui.backup_table.setHorizontalHeaderLabels([t("table_headers.name"), t("table_headers.date"), t("table_headers.size")])

		# Imposta modalità ridimensionamento colonne
		header = self.ui.backup_table.horizontalHeader()
		header.setSectionResizeMode(0, QHeaderView.Stretch)
		header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
		header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

		# Abilita selezione singola riga
		self.ui.backup_table.setSelectionBehavior(QAbstractItemView.SelectRows)

	def on_backup_row_selected(self):
		"""Chiamato quando viene selezionata una riga della tabella backup - mostra screenshot"""
		current_row = self.ui.backup_table.currentRow()
		if current_row < 0:
			return

		# Ottieni nome file backup dalla riga selezionata
		name_item = self.ui.backup_table.item(current_row, 0)
		if not name_item:
			return

		backup_filename = name_item.text()

		# Ottieni percorso cartella backup
		if not self.pyab.selected_profile:
			return

		profile = self.pyab.selected_profile
		if profile['backups_path'] == DEFAULT_BACKUP_PATH:
			backup_folder = PathBuilder.get_default_backup_path(
				profile['game_name'], profile['profile_name']
			)
		else:
			backup_folder = profile['backups_path']

		backup_file_path = os.path.join(backup_folder, backup_filename)

		# Estrai e mostra screenshot se presente
		self.show_screenshot_from_backup(backup_file_path)

	def show_screenshot_from_backup(self, zip_path):
		"""Estrae e visualizza screenshot da file zip backup"""
		try:
			if not os.path.exists(zip_path):
				self.ui.graphicsView.setScene(None)
				return

			with zipfile.ZipFile(zip_path, 'r') as zipf:
				names = zipf.namelist()
				screenshot_file = None
				for candidate in ('screenshot.jpg', 'screenshot.png'):
					if candidate in names:
						screenshot_file = candidate
						break

				if not screenshot_file:
					self.ui.graphicsView.setScene(None)
					return

				screenshot_data = zipf.read(screenshot_file)

			pixmap = QPixmap()
			pixmap.loadFromData(screenshot_data)

			if not pixmap.isNull():
				self._current_screenshot_pixmap = pixmap
				scene = QGraphicsScene()
				pixmap_item = QGraphicsPixmapItem(pixmap)
				scene.addItem(pixmap_item)
				self.ui.graphicsView.setScene(scene)
				self.ui.graphicsView.fitInView(pixmap_item, Qt.KeepAspectRatio)
			else:
				self._current_screenshot_pixmap = None
				self.ui.graphicsView.setScene(None)

		except Exception as e:
			logger.error(f"Error showing screenshot: {e}")
			self._current_screenshot_pixmap = None
			self.ui.graphicsView.setScene(None)

	def _on_screenshot_clicked(self, event):
		"""Apre popup con screenshot ingrandito al click sulla preview."""
		if not self._current_screenshot_pixmap:
			return

		from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
		from PySide6.QtCore import Qt

		dialog = QDialog(self.app)
		dialog.setWindowTitle("Screenshot")
		dialog.setMinimumSize(800, 500)
		dialog.resize(1024, 640)

		layout = QVBoxLayout(dialog)
		layout.setContentsMargins(0, 0, 0, 0)

		label = QLabel(dialog)
		label.setAlignment(Qt.AlignCenter)
		label.setStyleSheet("background-color: #121212;")

		# Scala al dialog mantenendo le proporzioni
		scaled = self._current_screenshot_pixmap.scaled(
			dialog.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
		)
		label.setPixmap(scaled)
		layout.addWidget(label)

		# Ridimensiona l'immagine quando si ridimensiona il dialog
		def on_resize(evt):
			if self._current_screenshot_pixmap:
				new_scaled = self._current_screenshot_pixmap.scaled(
					dialog.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
				)
				label.setPixmap(new_scaled)
			QDialog.resizeEvent(dialog, evt)

		dialog.resizeEvent = on_resize
		dialog.exec()

	def toggle_auto_backup(self):
		"""Avvia o ferma backup automatico"""
		if not self.pyab.selected_profile:
			from PySide6.QtWidgets import QMessageBox
			QMessageBox.warning(self.app, t("error"), t("select_profile_error"))
			return

		if self.auto_backup_active:
			self.stop_auto_backup()
		else:
			self.start_auto_backup()

	def start_auto_backup(self):
		if not self.pyab.selected_profile:
			return

		profile = self.pyab.selected_profile
		timer_seconds = profile.get('auto_backup_timer', 60)

		self.auto_backup_active = True
		self.ui.auto_backup_btn.setText(t("auto_backup_stop"))
		self.ui.auto_backup_btn.setStyleSheet(
			"QPushButton { background-color: #22c55e; color: #f0f0f0; }"
			"QPushButton:hover { background-color: #16a34a; }"
		)

		if timer_seconds == 0:
			self.start_file_monitoring()
			# AGGIUNGI: Timer per controllare stato gioco ogni 2 secondi
			self.game_status_timer = QTimer()
			self.game_status_timer.timeout.connect(self.check_game_status_periodic)
			self.game_status_timer.start(2000)  # Ogni 2 secondi
			self.ui.backup_updates.setText(t("auto_backup_watching"))
		else:
			# Modalità timer con countdown
			self.remaining_seconds = timer_seconds
			self.auto_backup_timer.start(timer_seconds * 1000)
			self.countdown_timer.start(1000)
			self.update_countdown()
			self.check_game_status()

	def stop_auto_backup(self):
		self.auto_backup_active = False
		self.auto_backup_timer.stop()
		self.countdown_timer.stop()

		# AGGIUNGI: Ferma anche il timer di controllo stato gioco
		if self.game_status_timer:
			self.game_status_timer.stop()

		self.ui.auto_backup_btn.setText(t("auto_backup_start"))
		self.ui.auto_backup_btn.setStyleSheet("")
		self.ui.backup_updates.setText(t("auto_backup_stopped"))

		# Ferma monitoraggio file se attivo
		if self.file_observer:
			try:
				self.file_observer.stop()
				self.file_observer.join(timeout=2)
				if self.file_observer.is_alive():
					logger.warning("File observer did not stop cleanly")
			except Exception as e:
				logger.error(f"Error stopping file observer: {e}")
			finally:
				self.file_observer = None

	def check_game_status_periodic(self):
		"""Controlla periodicamente stato gioco nella modalità file watcher"""
		if not self.auto_backup_active or not self.pyab.selected_profile:
			return

		game_exe = self.pyab.selected_profile.get('game_exe_name', '')
		if self.is_game_running(game_exe):
			self.ui.backup_updates.setText(t("auto_backup_watching"))
		else:
			self.ui.backup_updates.setText(t("auto_backup_paused"))

	def update_countdown(self):
		"""Aggiorna visualizzazione countdown"""
		if not self.auto_backup_active:
			return

		game_exe = self.pyab.selected_profile.get('game_exe_name', '')
		if self.is_game_running(game_exe):
			if self.remaining_seconds > 0:
				self.ui.backup_updates.setText(t("auto_backup_next", seconds=self.remaining_seconds))
				self.remaining_seconds -= 1
			else:
				# Reset countdown quando timer backup scatta
				timer_seconds = self.pyab.selected_profile.get('auto_backup_timer', 60)
				self.remaining_seconds = timer_seconds
		else:
			self.ui.backup_updates.setText(t("auto_backup_paused"))

	def start_file_monitoring(self):
		"""Avvia monitoraggio modifiche file salvataggio - VERSIONE MIGLIORATA"""
		if not self.pyab.selected_profile:
			return

		profile = self.pyab.selected_profile
		save_file_path = profile.get('save_file_path', '')

		# NUOVO: Logica per determinare quale file monitorare
		watch_file = profile.get('watch_file', '')  # Campo opzionale
		save_names_str = profile.get('save_name', '')

		if not save_file_path:
			self.ui.backup_updates.setText("Save file path not found")
			return

		# Determina quale file monitorare
		if watch_file:
			# Se esiste watch_file, usa quello
			file_to_watch = watch_file.strip()
		elif save_names_str:
			# Altrimenti usa il primo file della lista save_name
			save_names = [name.strip() for name in save_names_str.split(',') if name.strip()]
			if save_names:
				file_to_watch = save_names[0]  # Usa solo il primo
			else:
				self.ui.backup_updates.setText("No save files configured")
				return
		else:
			self.ui.backup_updates.setText("No files to watch configured")
			return

		save_file_path = PathBuilder.resolve_path_template(save_file_path)
		full_save_path = os.path.join(save_file_path, file_to_watch)

		logger.info(f"Setting up file monitoring for: {full_save_path}")

		# Controlla se il file esiste, ma non bloccare se non c'è
		if not os.path.exists(full_save_path):
			logger.warning(f"Save file not found at {full_save_path}, monitoring anyway...")
		# Non mostrare warning popup, solo log

		try:
			# Ferma observer esistente se presente
			if self.file_observer:
				try:
					self.file_observer.stop()
					self.file_observer.join(timeout=2)
				except (OSError, RuntimeError) as e:
					logger.error(f"Error stopping previous file observer: {e}")
				self.file_observer = None

			# Configura file watcher migliorato
			event_handler = FileWatcher(self._emit_file_modified_signal, full_save_path)
			self.file_observer = Observer()

			# Usa percorso assoluto della directory
			watch_dir = os.path.abspath(save_file_path)
			if not os.path.exists(watch_dir):
				self.ui.backup_updates.setText("Watch directory not found")
				return

			# Monitora la directory con ricorsione per catturare più eventi
			self.file_observer.schedule(event_handler, watch_dir, recursive=True)
			self.file_observer.start()

			logger.info(f"Started monitoring directory: {watch_dir}")
			logger.info(f"Watching specifically for file: {file_to_watch}")
			self.ui.backup_updates.setText(f"Watching {file_to_watch} for changes...")

		except Exception as e:
			self.ui.backup_updates.setText(f"Monitoring error: {str(e)}")
			logger.error(f"File monitoring error: {e}")

	def _handle_file_modification(self):
		if not self.auto_backup_active:
			return
		profile = self.pyab.selected_profile
		if not profile:
			return
		game_exe = profile.get('game_exe_name', '')
		if self.is_game_running(game_exe):
			self.ui.backup_updates.setText(t("file_modified_backup"))
			self.perform_backup()
		else:
			self.ui.backup_updates.setText(t("auto_backup_paused"))

	def on_save_file_modified(self):
		self._handle_file_modification()

	def check_and_backup(self):
		"""Controlla se gioco è in esecuzione e crea backup se necessario"""
		if not self.auto_backup_active or not self.pyab.selected_profile:
			return

		game_exe = self.pyab.selected_profile.get('game_exe_name', '')
		if self.is_game_running(game_exe):
			self.ui.backup_updates.setText(t("auto_backup_creating"))
			self.perform_backup()

			# Reset countdown
			timer_seconds = self.pyab.selected_profile.get('auto_backup_timer', 60)
			self.remaining_seconds = timer_seconds
		else:
			self.ui.backup_updates.setText(t("auto_backup_paused"))

	def check_game_status(self):
		"""Controlla stato gioco senza creare backup"""
		if not self.pyab.selected_profile:
			return

		game_exe = self.pyab.selected_profile.get('game_exe_name', '')
		if self.is_game_running(game_exe):
			if self.pyab.selected_profile.get('auto_backup_timer', 60) == 0:
				self.ui.backup_updates.setText(t("auto_backup_watching"))
			else:
				timer_seconds = self.pyab.selected_profile.get('auto_backup_timer', 60)
				self.ui.backup_updates.setText(t("auto_backup_next", seconds=timer_seconds))
		else:
			self.ui.backup_updates.setText(t("auto_backup_paused"))

	def is_game_running(self, exe_name):
		"""Controlla se processo gioco è in esecuzione"""
		if not exe_name:
			return False

		try:
			for proc in psutil.process_iter(['name']):
				if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
					return True
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass

		return False

	def on_backup_thread_finished(self):
		"""Cleanup backup thread quando finito"""
		if self.backup_worker:
			self.backup_worker.deleteLater()
			self.backup_worker = None

	def update_backup_status(self, message):
		"""Aggiorna stato backup"""
		self.ui.backup_updates.setText(message)

	def on_backup_completed(self, success, message):
		if success:
			self.ui.backup_updates.setText(t("backup_completed"))
			self.refresh_backup_table()
			self.update_profile_stats()
		else:
			QMessageBox.critical(self.app, t("error"), t("backup_error", message=message))

	def update_profile_stats(self):
		"""Aggiorna statistiche profilo dopo completamento backup"""
		if not self.pyab.selected_profile:
			return

		profile = self.pyab.selected_profile

		# Determina percorso backup
		if profile['backups_path'] == DEFAULT_BACKUP_PATH:
			backup_path = PathBuilder.get_default_backup_path(profile['game_name'], profile['profile_name'])
		else:
			backup_path = profile['backups_path']

		# Aggiorna label conteggio file e dimensione
		n_files, size = self.analyze_backup_folder(backup_path)
		self.ui.files_found.setText(f"{n_files}/{profile['max_backups_files']}")
		self.ui.weight_found.setText(f"{size}/{profile['max_size_files']} MB")

	def cleanup_old_backups(self, backup_folder, max_files, max_size_mb):
		try:
			profile = self.pyab.selected_profile
			game_name = profile['game_name']
			profile_name = profile['profile_name']  # Aggiungi questo
			# Modifica: pattern senza save_name
			pattern = rf"{re.escape(game_name)}_{re.escape(profile_name)}_\d+_\d+\.zip"

			backup_files = []
			for filename in os.listdir(backup_folder):
				filepath = os.path.join(backup_folder, filename)
				if os.path.isfile(filepath) and re.match(pattern, filename, re.IGNORECASE):
					stat = os.stat(filepath)
					backup_files.append({
						'path': filepath,
						'date': datetime.datetime.fromtimestamp(stat.st_mtime),
						'size': stat.st_size
					})

			# Ordina per data (più vecchi prima per eliminazione)
			backup_files.sort(key=lambda x: x['date'])

			# Rimuovi file in eccesso (mantieni max_files più recenti)
			while len(backup_files) > max_files:
				oldest_file = backup_files.pop(0)
				os.remove(oldest_file['path'])
				logger.info(f"Removed old backup: {oldest_file['path']}")

			# Rimuovi file per rispettare limite dimensione
			total_size_mb = sum(f['size'] for f in backup_files) / (1024 * 1024)
			while total_size_mb > max_size_mb and backup_files:
				oldest_file = backup_files.pop(0)
				total_size_mb -= oldest_file['size'] / (1024 * 1024)
				os.remove(oldest_file['path'])
				self.invalidate_analysis_cache(backup_folder)
				logger.info(f"Removed backup for size limit: {oldest_file['path']}")

		except Exception as e:
			logger.error(f"Error during backup cleanup: {e}")

	def create_backup(self):
		"""Crea backup di file salvataggio (supporta multipli file separati da virgola)"""
		try:
			profile = self.pyab.selected_profile
			if not profile:
				return False, "No profile selected"

			# Costruisci percorso file salvataggio
			save_file_path = profile.get('save_file_path', '')
			save_names_str = profile.get('save_name', '')  # Può contenere più nomi separati da virgola
			save_file_path = PathBuilder.resolve_path_template(save_file_path)

			if not save_file_path or not save_names_str:
				return False, "Save file path not configured"

			# Splitta i nomi file per supporto multi-file
			save_names = [name.strip() for name in save_names_str.split(',') if name.strip()]

			# Verifica che almeno un file esista
			existing_files = []
			for save_name in save_names:
				full_save_path = os.path.join(save_file_path, save_name)
				if os.path.exists(full_save_path):
					existing_files.append((save_name, full_save_path))

			if not existing_files:
				return False, "No save files found"

			# Determina cartella backup
			if profile['backups_path'] == DEFAULT_BACKUP_PATH:
				backup_folder = PathBuilder.get_default_backup_path(
					profile['game_name'], profile['profile_name']
				)
			else:
				backup_folder = profile['backups_path']

			# Crea cartella se non esiste
			Path(backup_folder).mkdir(parents=True, exist_ok=True)

			# Pulisci vecchi backup prima di creare nuovo
			max_files = profile.get('max_backups_files', 10)
			max_size_mb = profile.get('max_size_files', 100)
			self.cleanup_old_backups(backup_folder, max_files, max_size_mb)

			# Cambia questa parte nel metodo create_backup:
			game_name = profile['game_name']
			profile_name = profile['profile_name']  # Aggiungi questo
			timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
			zip_name = f"{game_name}_{profile_name}_{timestamp}.zip"  # Modifica: non usa più save_name
			zip_path = os.path.join(backup_folder, zip_name)

			# Crea file zip con tutti i file esistenti
			with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
				# Aggiungi tutti i file di salvataggio esistenti
				for save_name, full_path in existing_files:
					zipf.write(full_path, save_name)

				# Aggiungi screenshot se richiesto
				if profile.get('screenshot', False):
					screenshot_path = self.capture_game_screenshot()
					if screenshot_path:
						zipf.write(screenshot_path, "screenshot.jpg")
						os.remove(screenshot_path)

			self.invalidate_analysis_cache(backup_folder)
			return True, f"Backup created with {len(existing_files)} files"

		except Exception as e:
			return False, f"Error during backup creation: {str(e)}"

	def capture_game_screenshot(self):
		"""Cattura screenshot del monitor su cui si trova il gioco tramite mss."""
		try:
			profile = self.pyab.selected_profile
			game_exe = profile.get('game_exe_name', '') if profile else ''

			monitor_idx = _find_game_monitor_index(game_exe)

			temp_dir = tempfile.gettempdir()
			filename = f'screenshot_{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}.png'
			filepath = os.path.join(temp_dir, filename)

			with mss.mss() as sct:
				monitor = sct.monitors[monitor_idx]
				img = sct.grab(monitor)
				mss.tools.to_png(img.rgb, img.size, output=filepath)

			# Converti in JPEG per ridurre dimensione
			from PIL import Image
			with Image.open(filepath) as im:
				jpg_path = filepath.replace('.png', '.jpg')
				im.convert("RGB").save(jpg_path, "JPEG", quality=60)
			os.remove(filepath)

			return jpg_path

		except Exception as e:
			logger.error(f"Error capturing screenshot: {e}")
			return None

	def refresh_backup_table(self):
		"""Aggiorna tabella backup"""
		if not self.pyab.selected_profile:
			self.ui.backup_table.setRowCount(0)
			return

		profile = self.pyab.selected_profile

		# Determina cartella backup
		if profile['backups_path'] == DEFAULT_BACKUP_PATH:
			backup_folder = PathBuilder.get_default_backup_path(
				profile['game_name'], profile['profile_name']
			)
		else:
			backup_folder = profile['backups_path']

		if not os.path.exists(backup_folder):
			self.ui.backup_table.setRowCount(0)
			return

		game_name = profile['game_name']
		profile_name = profile['profile_name']  # NUOVO: usa profile_name invece di save_name

		# MODIFICA: pattern senza save_name, solo game_name_profile_name_timestamp.zip
		pattern = rf"{re.escape(game_name)}_{re.escape(profile_name)}_\d{{8}}_\d{{6}}\.zip"

		backup_files = []
		try:
			for filename in os.listdir(backup_folder):
				filepath = os.path.join(backup_folder, filename)
				if os.path.isfile(filepath) and re.match(pattern, filename, re.IGNORECASE):
					stat = os.stat(filepath)
					backup_files.append({
						'name': filename,
						'date': datetime.datetime.fromtimestamp(stat.st_mtime),
						'size': stat.st_size,
						'path': filepath
					})
		except Exception as e:
			logger.error(f"Error reading backups: {e}")
			self.ui.backup_table.setRowCount(0)
			return

		# Ordina per data (più recenti prima)
		backup_files.sort(key=lambda x: x['date'], reverse=True)

		# Popola tabella
		self.ui.backup_table.setRowCount(len(backup_files))
		for row, backup in enumerate(backup_files):
			# Nome
			name_item = QTableWidgetItem(backup['name'])
			self.ui.backup_table.setItem(row, 0, name_item)

			# Data
			date_str = backup['date'].strftime("%d/%m/%Y %H:%M")
			date_item = QTableWidgetItem(date_str)
			self.ui.backup_table.setItem(row, 1, date_item)

			# Dimensione
			size_mb = backup['size'] / (1024 * 1024)
			size_str = f"{size_mb:.2f} MB"
			size_item = QTableWidgetItem(size_str)
			self.ui.backup_table.setItem(row, 2, size_item)

	def invalidate_analysis_cache(self, backup_path=None):
		"""Invalida la cache dell'analisi backup. Se backup_path è None, invalida tutta la cache."""
		if backup_path:
			self._analysis_cache.pop(backup_path, None)
		else:
			self._analysis_cache.clear()

	def analyze_backup_folder(self, backup_path):
		if not os.path.exists(backup_path):
			return 0, 0.0

		# Controlla cache (valida per 5 secondi)
		import time
		now = time.time()
		cached = self._analysis_cache.get(backup_path)
		if cached:
			n_files, size_mb, cache_time = cached
			if now - cache_time < 5:
				return n_files, size_mb

		game_name = self.pyab.selected_profile['game_name']
		profile_name = self.pyab.selected_profile['profile_name']
		pattern = rf"{re.escape(game_name)}_{re.escape(profile_name)}_\d+_\d+\.zip"

		zip_count = 0
		total_size_bytes = 0

		try:
			for filename in os.listdir(backup_path):
				filepath = os.path.join(backup_path, filename)
				if os.path.isfile(filepath):
					if re.match(pattern, filename, re.IGNORECASE):
						zip_count += 1
						total_size_bytes += os.path.getsize(filepath)
		except PermissionError:
			return 0, 0.0
		except Exception as e:
			logger.error(f"Error during backup folder analysis: {e}")
			return 0, 0.0

		total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
		self._analysis_cache[backup_path] = (zip_count, total_size_mb, now)
		return zip_count, total_size_mb

	def _emit_file_modified_signal(self):
		self.file_modified_signal.emit()

	def perform_backup(self):
		perform_backup(self)

	def backup_now(self):
		"""Esegue un backup manuale immediato, senza richiedere che il gioco sia attivo."""
		if not self.pyab.selected_profile:
			QMessageBox.warning(self.app, t("error"), t("select_profile_error"))
			return
		if self.backup_worker and self.backup_worker.isRunning():
			return
		self.ui.backup_now_btn.setEnabled(False)
		self.ui.backup_updates.setText(t("manual_backup_progress"))
		success, message = self.create_backup()
		self.on_backup_completed(success, message)
		self.ui.backup_now_btn.setEnabled(True)

	def delete_selected_backup(self):
		"""Elimina il backup selezionato nella tabella"""
		current_row = self.ui.backup_table.currentRow()
		if current_row < 0:
			QMessageBox.warning(self.app, t("warning"), t("select_backup_delete"))
			return

		# Ottieni nome file backup dalla riga selezionata
		name_item = self.ui.backup_table.item(current_row, 0)
		if not name_item:
			return

		backup_filename = name_item.text()

		# Conferma eliminazione
		reply = QMessageBox.question(
			self.app,
			t("confirm_delete"),
			f"Are you sure you want to delete the backup '{backup_filename}'?\n\nThis action cannot be undone.",
			QMessageBox.Yes | QMessageBox.No,
			QMessageBox.No
		)

		if reply != QMessageBox.Yes:
			return

		try:
			# Ottieni percorso cartella backup
			if not self.pyab.selected_profile:
				QMessageBox.warning(self.app, t("error"), t("no_profile_selected"))
				return

			profile = self.pyab.selected_profile

			if profile['backups_path'] == DEFAULT_BACKUP_PATH:
				backup_folder = PathBuilder.get_default_backup_path(
					profile['game_name'], profile['profile_name']
				)
			else:
				backup_folder = profile['backups_path']

			backup_file_path = os.path.join(backup_folder, backup_filename)

			# Elimina il file
			if os.path.exists(backup_file_path):
				os.remove(backup_file_path)
				self.invalidate_analysis_cache()

				# Aggiorna tabella e statistiche
				self.refresh_backup_table()
				self.update_profile_stats()

				QMessageBox.information(self.app, t("success"), f"Backup '{backup_filename}' deleted successfully.")
			else:
				QMessageBox.warning(self.app, t("error"), t("backup_not_found"))

		except Exception as e:
			QMessageBox.critical(self.app, t("error"), f"Failed to delete backup: {str(e)}")

	def delete_all_backups(self):
		"""Elimina tutti i backup nella cartella del profilo"""
		if not self.pyab.selected_profile:
			QMessageBox.warning(self.app, t("error"), t("no_profile_selected"))
			return

		profile = self.pyab.selected_profile

		# Ottieni percorso cartella backup
		if profile['backups_path'] == DEFAULT_BACKUP_PATH:
			backup_folder = PathBuilder.get_default_backup_path(
				profile['game_name'], profile['profile_name']
			)
		else:
			backup_folder = profile['backups_path']

		if not os.path.exists(backup_folder):
			QMessageBox.information(self.app, t("info"), t("no_backup_folder"))
			return

		# Conta i backup esistenti
		game_name = profile['game_name']
		profile_name = profile['profile_name']
		pattern = rf"{re.escape(game_name)}_{re.escape(profile_name)}_\d+_\d+\.zip"

		backup_count = 0
		try:
			for filename in os.listdir(backup_folder):
				file_path = os.path.join(backup_folder, filename)
				if os.path.isfile(file_path) and re.match(pattern, filename, re.IGNORECASE):
					backup_count += 1

		except Exception as e:
			logger.error(f"Error counting backups: {e}")
			backup_count = 0

		if backup_count == 0:
			QMessageBox.information(self.app, t("info"), t("no_backups_found"))
			return

		# Conferma eliminazione
		reply = QMessageBox.question(
			self.app,
			t("confirm_delete_all"),
			f"Are you sure you want to delete ALL {backup_count} backups for this profile?\n\nThis action cannot be undone.",
			QMessageBox.Yes | QMessageBox.No,
			QMessageBox.No
		)

		if reply != QMessageBox.Yes:
			return

		try:
			deleted_count = 0

			for filename in os.listdir(backup_folder):
				file_path = os.path.join(backup_folder, filename)
				if os.path.isfile(file_path) and re.match(pattern, filename, re.IGNORECASE):
					os.remove(file_path)
					deleted_count += 1

			self.invalidate_analysis_cache()

			# Aggiorna tabella e statistiche
			self.refresh_backup_table()
			self.update_profile_stats()

			QMessageBox.information(self.app, t("success"), f"Successfully deleted {deleted_count} backups.")

		except Exception as e:
			QMessageBox.critical(self.app, t("error"), f"Failed to delete backups: {str(e)}")

	def restore_selected_backup(self):
		"""Ripristina il backup selezionato dalla tabella (supporta multipli file)"""
		current_row = self.ui.backup_table.currentRow()
		if current_row < 0:
			QMessageBox.warning(self.app, t("warning"), t("select_backup_restore"))
			return

		# Ottieni nome file backup dalla riga selezionata
		name_item = self.ui.backup_table.item(current_row, 0)
		if not name_item:
			return

		backup_filename = name_item.text()

		if not self.pyab.selected_profile:
			QMessageBox.warning(self.app, t("error"), t("no_profile_selected"))
			return

		profile = self.pyab.selected_profile

		# Conferma ripristino
		reply = QMessageBox.question(
			self.app,
			t("confirm_restore"),
			f"Are you sure you want to restore the backup '{backup_filename}'?\n\nThis will overwrite your current save files.",
			QMessageBox.Yes | QMessageBox.No,
			QMessageBox.No
		)

		if reply != QMessageBox.Yes:
			return

		try:
			# Ottieni percorso cartella backup
			if profile['backups_path'] == DEFAULT_BACKUP_PATH:
				backup_folder = PathBuilder.get_default_backup_path(
					profile['game_name'], profile['profile_name']
				)
			else:
				backup_folder = profile['backups_path']

			backup_file_path = os.path.join(backup_folder, backup_filename)

			if not os.path.exists(backup_file_path):
				QMessageBox.warning(self.app, t("error"), t("backup_not_found"))
				return

			# Ottieni percorso file salvataggio
			save_file_path = profile.get('save_file_path', '')
			save_names_str = profile.get('save_name', '')

			if not save_file_path or not save_names_str:
				QMessageBox.warning(self.app, t("error"), "Save file path not configured in profile.")
				return

			save_file_path = PathBuilder.resolve_path_template(save_file_path)
			save_names = [name.strip() for name in save_names_str.split(',') if name.strip()]

			# Crea cartella di destinazione se non esiste
			os.makedirs(save_file_path, exist_ok=True)

			# Estrai il backup
			restored_files = []
			with zipfile.ZipFile(backup_file_path, 'r') as zipf:
				available_files = zipf.namelist()

				# Ripristina tutti i file di salvataggio presenti nel backup
				for save_name in save_names:
					if save_name in available_files:
						full_save_path = os.path.join(save_file_path, save_name)

						# Crea backup del file corrente se esiste
						if os.path.exists(full_save_path):
							backup_current = full_save_path + ".backup_before_restore"
							shutil.copy2(full_save_path, backup_current)

						# Estrai il file
						zipf.extract(save_name, save_file_path)
						restored_files.append(save_name)

			if restored_files:
				files_list = ", ".join(restored_files)
				QMessageBox.information(
					self.app,
					t("success"),
					f"Backup '{backup_filename}' restored successfully.\n\nRestored files: {files_list}"
				)
			else:
				QMessageBox.warning(
					self.app,
					"Warning",
					"No matching save files found in backup to restore."
				)

		except Exception as e:
			QMessageBox.critical(self.app, t("error"), f"Failed to restore backup: {str(e)}")

	def show_backup_context_menu(self, position: QPoint):
		"""Mostra context menu quando si clicca tasto destro sulla tabella backup"""
		if self.ui.backup_table.itemAt(position) is None:
			return  # Non mostrare menu se clic su area vuota

		context_menu = QMenu(self.ui.backup_table)

		# Azioni del context menu
		restore_action = QAction(t("context_menu.restore"), self.ui.backup_table)
		restore_action.triggered.connect(self.restore_selected_backup)

		open_folder_action = QAction(t("context_menu.open_folder"), self.ui.backup_table)
		open_folder_action.triggered.connect(self.open_backup_folder)

		delete_selected_action = QAction(t("context_menu.delete_selected"), self.ui.backup_table)
		delete_selected_action.triggered.connect(self.delete_selected_backup)

		delete_all_action = QAction(t("context_menu.delete_all"), self.ui.backup_table)
		delete_all_action.triggered.connect(self.delete_all_backups)

		# Aggiungi azioni al menu
		context_menu.addAction(restore_action)
		context_menu.addSeparator()
		context_menu.addAction(open_folder_action)
		context_menu.addSeparator()
		context_menu.addAction(delete_selected_action)
		context_menu.addAction(delete_all_action)

		# Mostra menu
		context_menu.exec(self.ui.backup_table.mapToGlobal(position))

	def open_backup_folder(self):
		"""Apre la cartella dei backup in Esplora File"""
		if not self.pyab.selected_profile:
			QMessageBox.warning(self.app, t("error"), t("no_profile_selected"))
			return

		profile = self.pyab.selected_profile

		# Ottieni percorso cartella backup
		if profile['backups_path'] == DEFAULT_BACKUP_PATH:
			backup_folder = PathBuilder.get_default_backup_path(
				profile['game_name'], profile['profile_name']
			)
		else:
			backup_folder = profile['backups_path']

		if not os.path.exists(backup_folder):
			QMessageBox.warning(self.app, t("error"), "Backup folder does not exist.")
			return

		# Apri cartella in Esplora File
		QDesktopServices.openUrl(QUrl.fromLocalFile(backup_folder))
