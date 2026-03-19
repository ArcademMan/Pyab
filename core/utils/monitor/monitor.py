import win32api


class ScreenUtils:
	@classmethod
	def get_screen_count(cls):
		"""Ritorna il numero di schermi disponibili"""
		return win32api.GetSystemMetrics(80)  # SM_CMONITORS

	@classmethod
	def get_available_screens(cls):
		"""Versione semplificata senza EnumDisplayMonitors"""
		screen_count = cls.get_screen_count()

		screens_info = {
			'count': screen_count,
			'primary': 0,
			'screens': []
		}

		# Crea info base per ogni schermo
		for i in range(screen_count):
			screen_data = {
				'index': i,
				'name': f"Screen {i + 1}",
				'device_name': f'\\\\.\\DISPLAY{i + 1}',
				'is_primary': i == 0  # Assume primo schermo = primario
			}
			screens_info['screens'].append(screen_data)

		return screens_info

	@classmethod
	def get_screen_names(cls):
		screens_info = cls.get_available_screens()
		return [screen['name'] for screen in screens_info['screens']]

	@classmethod
	def get_primary_screen_index(cls):
		return 0  # Assume primo schermo = primario
