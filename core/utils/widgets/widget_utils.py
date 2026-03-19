import logging
from pathlib import Path
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPixmap, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLayout, QLayoutItem

logger = logging.getLogger(__name__)

class BackgroundWidget(QWidget):
    def __init__(self, parent=None, image_path: str = None, bg_color: QColor = None):
        super().__init__(parent)
        self._pixmap = None
        self._bg_color = bg_color
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        if image_path:
            self.setBackgroundImage(image_path)

    def setBackgroundImage(self, image_path) -> bool:
        p = Path(image_path).resolve().as_posix()
        pm = QPixmap(p)
        if pm.isNull():
            logger.warning(f"BackgroundWidget: unable to load image: {p}")
            self._pixmap = None
            self.update()
            return False
        self._pixmap = pm
        self.update()
        return True

    def setBackgroundColor(self, color: QColor):
        self._bg_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        if self._bg_color is not None:
            painter.fillRect(rect, self._bg_color)

        if self._pixmap:
            scaled = self._pixmap.scaled(rect.size(),
                                         Qt.KeepAspectRatioByExpanding,
                                         Qt.SmoothTransformation)
            x = (rect.width()  - scaled.width()) // 2
            y = (rect.height() - scaled.height()) // 2
            painter.drawPixmap(QRect(x, y, scaled.width(), scaled.height()), scaled)

        # lascia che Qt disegni correttamente i child e lo stile
        super().paintEvent(event)

class WidgetUtils:
    @staticmethod
    def _move_layout_items(src_layout: QLayout, dst_layout: QLayout):
        # sposta tutti gli item (widget o sub-layout) senza distruggere il layout sorgente
        while src_layout.count():
            item: QLayoutItem = src_layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(dst_layout.parentWidget())
                dst_layout.addWidget(w)
            elif item.layout():
                sub = item.layout()
                # reparent del sublayout e aggiunta al nuovo container
                sub.setParent(dst_layout.parent())
                dst_layout.addLayout(sub)
            # gli spacerItem si possono ricreare o ignorare (spesso non servono più)
            # elif item.spacerItem(): pass

    @staticmethod
    def replace_placeholder_with_background(container_parent: QWidget,
                                            image_path: str,
                                            placeholder_name: str = "background_placeholder") -> BackgroundWidget:
        ph = container_parent.findChild(QWidget, placeholder_name)
        if ph is None:
            logger.warning(f"Placeholder '{placeholder_name}' not found.")
            return None

        parent = ph.parentWidget()
        parent_layout = parent.layout() if parent else None
        if parent_layout is None:
            logger.warning("Parent has no layout: cannot safely replace placeholder.")
            return None

        # crea nuovo contenitore
        bg = BackgroundWidget(parent=parent, image_path=image_path)
        bg.setObjectName(ph.objectName() or "background_container")
        bg.setMinimumSize(ph.minimumSize())
        bg.setMaximumSize(ph.maximumSize())
        bg.setSizePolicy(ph.sizePolicy())

        # sposta gli item del layout del placeholder nel nuovo bg
        ph_layout = ph.layout()
        if ph_layout:
            WidgetUtils._move_layout_items(ph_layout, bg.layout())

        # sposta eventuali figli diretti che non sono nel layout (per sicurezza)
        for child in ph.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            child.setParent(bg)
            bg.layout().addWidget(child)

        # rimpiazza ph nel layout del parent mantenendo la posizione
        idx = parent_layout.indexOf(ph)
        parent_layout.insertWidget(idx, bg)
        parent_layout.removeWidget(ph)
        ph.setParent(None)
        ph.deleteLater()  # evita dangling pointers

        return bg
