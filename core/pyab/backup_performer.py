from core.pyab.backup_worker import BackupWorker


def perform_backup(backup_manager):
	if backup_manager.backup_worker and backup_manager.backup_worker.isRunning():
		return

	if backup_manager.backup_worker:
		backup_manager.backup_worker.quit()
		backup_manager.backup_worker.wait(1000)
		backup_manager.backup_worker = None

	backup_manager.backup_worker = BackupWorker(backup_manager)
	backup_manager.backup_worker.backup_completed.connect(backup_manager.on_backup_completed)
	backup_manager.backup_worker.status_update.connect(backup_manager.update_backup_status)
	backup_manager.backup_worker.finished.connect(backup_manager.on_backup_thread_finished)
	backup_manager.backup_worker.start()