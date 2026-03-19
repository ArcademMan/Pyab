import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class FileWatcher(FileSystemEventHandler):
	def __init__(self, callback, file_path):
		super().__init__()
		self.callback = callback
		self.file_path = Path(file_path).resolve()
		self.file_name = self.file_path.name
		self.last_trigger = 0  # Evita trigger multipli
		self.debounce_time = 2  # Secondi di debounce

	def on_modified(self, event):
		try:
			# Ignora modifiche alle directory
			if event.is_directory:
				return

			modified_path = Path(event.src_path).resolve()

			# Controlla sia il path completo che solo il nome file
			if (modified_path == self.file_path or
					modified_path.name == self.file_name):

				# Debounce per evitare trigger multipli
				current_time = time.time()
				if current_time - self.last_trigger < self.debounce_time:
					return

				self.last_trigger = current_time
				self.callback()

		except (OSError, ValueError) as e:
			logger.error(f"Error in FileWatcher on_modified: {e}")

	def on_created(self, event):
		if not event.is_directory:
			self.on_modified(event)

	def on_moved(self, event):
		if not event.is_directory:
			try:
				dest_path = Path(event.dest_path).resolve()
				if (dest_path == self.file_path or
						dest_path.name == self.file_name):
					self.callback()
			except (OSError, ValueError) as e:
				logger.error(f"Error in FileWatcher on_moved: {e}")
