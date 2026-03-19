import logging

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class BackupWorker(QThread):
	backup_completed = Signal(bool, str)
	status_update = Signal(str)

	def __init__(self, backup_manager):
		super().__init__()
		self.backup_manager = backup_manager
		# Snapshot del profilo al momento della creazione per thread safety
		self.profile_snapshot = (backup_manager.pyab.selected_profile or {}).copy()
		self.running = False

	def run(self):
		self.running = True
		profile = self.profile_snapshot

		if not profile:
			self.backup_completed.emit(False, "Nessun profilo selezionato")
			return

		try:
			# Controlla se il processo del gioco è in esecuzione
			game_exe = profile.get('game_exe_name', '')
			if not self.backup_manager.is_game_running(game_exe):
				self.status_update.emit("In pausa - Gioco non in esecuzione")
				self.backup_completed.emit(False, "Gioco non in esecuzione")
				return

			self.status_update.emit("Creazione backup in corso...")

			# Crea il backup
			success, message = self.backup_manager.create_backup()
			self.backup_completed.emit(success, message)

		except Exception as e:
			logger.error(f"Error during backup: {e}")
			self.backup_completed.emit(False, f"Errore durante il backup: {str(e)}")
		finally:
			self.running = False
