from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt

class ImageCache:
    _pixmap_cache = {}
    _icon_cache = {}

    @classmethod
    def get_scaled_pixmap(cls, filepath: str, width: int = None, height: int = None) -> QPixmap:
        cache_key = (filepath, width, height)
        if cache_key in cls._pixmap_cache:
            return cls._pixmap_cache[cache_key]

        pm = QPixmap(filepath)
        if pm.isNull():
            return QPixmap()

        if width is not None and height is not None:
            pm = pm.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        cls._pixmap_cache[cache_key] = pm
        return pm

    @classmethod
    def get_scaled_icon(cls, filepath: str, width: int = None, height: int = None) -> QIcon:
        cache_key = (filepath, width, height)
        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]

        pixmap = QPixmap(filepath)
        if pixmap.isNull():
            return QIcon()

        if width is not None and height is not None:
            pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        icon = QIcon(pixmap)
        cls._icon_cache[cache_key] = icon
        return icon
