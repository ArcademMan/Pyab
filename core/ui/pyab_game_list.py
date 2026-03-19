# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtGui, QtWidgets

_PATH_SHORTCUTS_TOOLTIP = """<html><body style="color: #f0f0f0; background-color: #252525; padding: 8px;">
<p style="font-weight: bold; font-size: 13px; margin-bottom: 6px;">Path Shortcuts</p>
<table cellspacing="4">
<tr><td style="color: #3b82f6; font-weight: bold;">#Documents#</td><td>Documents folder</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#AppData#</td><td>AppData root (parent of Roaming)</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#UserName#</td><td>User profile directory</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#Steam#</td><td>Steam installation folder</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#Ubisoft#</td><td>Ubisoft Game Launcher folder</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#PYAB#</td><td>PyAB program directory</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#GAME_NAME#</td><td>Current game name</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#PROFILE_NAME#</td><td>Current profile name</td></tr>
<tr><td style="color: #3b82f6; font-weight: bold;">#ID#</td><td>First subfolder found (e.g. Steam user ID)</td></tr>
</table>
<p style="color: #71717a; margin-top: 6px;">Shortcuts are not case-sensitive.<br/>Example: #Documents#\\NBGI\\DARK SOULS REMASTERED\\#ID#</p>
</body></html>"""

_WATCH_FILE_TOOLTIP = """<html><body style="color: #f0f0f0; background-color: #252525; padding: 8px;">
<p style="font-weight: bold; font-size: 13px; margin-bottom: 6px;">Watch File</p>
<p>Some games use multiple save files but update a single index file whenever any save changes.<br/>
Set the <b>Watch File</b> to that index file, and PyAB will create a backup of all other save files when it changes.</p>
<p style="color: #71717a; margin-top: 6px;"><b>Example (Silent Hill f):</b><br/>
Watch File: SaveSlotSystem.sav<br/>
Files to backup: SaveSlot100.sav, SaveSlot101.sav, SaveSlot102.sav</p>
</body></html>"""

_INFO_BTN_STYLE = """
    QToolButton {
        background-color: #2a2a2a;
        color: #3b82f6;
        border: 1px solid #333333;
        border-radius: 10px;
        font-weight: bold;
        font-size: 12px;
        margin-left: 4px;
        margin-right: 4px;
        min-width: 20px;
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
    }
    QToolButton:hover {
        background-color: #3b82f6;
        color: #f0f0f0;
    }
"""


def _make_info_btn(parent, tooltip):
    btn = QtWidgets.QToolButton(parent)
    btn.setText("i")
    btn.setToolTip(tooltip)
    btn.setStyleSheet(_INFO_BTN_STYLE)
    btn.clicked.connect(lambda: QtWidgets.QToolTip.showText(
        btn.mapToGlobal(btn.rect().bottomLeft()), tooltip, btn
    ))
    return btn


class Ui_GameList(object):
    def setupUi(self, GameList):
        GameList.setObjectName("GameList")
        GameList.resize(1180, 540)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(GameList)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.game_list_filter = QtWidgets.QLineEdit(GameList)
        self.game_list_filter.setText("")
        self.game_list_filter.setObjectName("game_list_filter")
        self.verticalLayout.addWidget(self.game_list_filter)
        self.listWidget = QtWidgets.QListWidget(GameList)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.create_new_btn = QtWidgets.QPushButton(GameList)
        self.create_new_btn.setObjectName("create_new_btn")
        self.horizontalLayout_5.addWidget(self.create_new_btn)
        self.dupe_selected_btn = QtWidgets.QPushButton(GameList)
        self.dupe_selected_btn.setObjectName("dupe_selected_btn")
        self.horizontalLayout_5.addWidget(self.dupe_selected_btn)
        self.delete_selected_btn = QtWidgets.QPushButton(GameList)
        self.delete_selected_btn.setObjectName("delete_selected_btn")
        self.horizontalLayout_5.addWidget(self.delete_selected_btn)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_4.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setVerticalSpacing(10)
        self.formLayout.setObjectName("formLayout")
        self.label_8 = QtWidgets.QLabel(GameList)
        self.label_8.setText("")
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_8)
        self.label = QtWidgets.QLabel(GameList)
        self.label.setObjectName("label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.name = QtWidgets.QLineEdit(GameList)
        self.name.setObjectName("name")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.name)
        self.label_2 = QtWidgets.QLabel(GameList)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.file_name = QtWidgets.QLineEdit(GameList)
        self.file_name.setObjectName("file_name")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.file_name)
        self.label_3 = QtWidgets.QLabel(GameList)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.exe_name = QtWidgets.QLineEdit(GameList)
        self.exe_name.setObjectName("exe_name")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.exe_name)
        self.label_4 = QtWidgets.QLabel(GameList)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.save_file_path = QtWidgets.QLineEdit(GameList)
        self.save_file_path.setObjectName("save_file_path")
        self.horizontalLayout.addWidget(self.save_file_path)
        self.horizontalLayout.addWidget(_make_info_btn(GameList, _PATH_SHORTCUTS_TOOLTIP))
        self.save_file_path_btn = QtWidgets.QToolButton(GameList)
        self.save_file_path_btn.setObjectName("save_file_path_btn")
        self.horizontalLayout.addWidget(self.save_file_path_btn)
        self.formLayout.setLayout(4, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout)
        self.label_5 = QtWidgets.QLabel(GameList)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.backup_path = QtWidgets.QLineEdit(GameList)
        self.backup_path.setObjectName("backup_path")
        self.horizontalLayout_2.addWidget(self.backup_path)
        self.horizontalLayout_2.addWidget(_make_info_btn(GameList, _PATH_SHORTCUTS_TOOLTIP))
        self.backup_path_btn = QtWidgets.QToolButton(GameList)
        self.backup_path_btn.setObjectName("backup_path_btn")
        self.horizontalLayout_2.addWidget(self.backup_path_btn)
        self.formLayout.setLayout(5, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.label_7 = QtWidgets.QLabel(GameList)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.icon = QtWidgets.QLineEdit(GameList)
        self.icon.setObjectName("icon")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.icon)
        self.label_6 = QtWidgets.QLabel(GameList)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.note = QtWidgets.QPlainTextEdit(GameList)
        self.note.setObjectName("note")
        self.horizontalLayout_6.addWidget(self.note)
        self.game_icon = QtWidgets.QLabel(GameList)
        self.game_icon.setText("")
        self.game_icon.setObjectName("game_icon")
        self.horizontalLayout_6.addWidget(self.game_icon)
        self.formLayout.setLayout(8, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_6)
        self.label_9 = QtWidgets.QLabel(GameList)
        self.label_9.setObjectName("label_9")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.label_9)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.watch_line_edit = QtWidgets.QLineEdit(GameList)
        self.watch_line_edit.setObjectName("watch_line_edit")
        self.horizontalLayout_7.addWidget(self.watch_line_edit)
        self.horizontalLayout_7.addWidget(_make_info_btn(GameList, _WATCH_FILE_TOOLTIP))
        self.formLayout.setLayout(7, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_7)
        self.verticalLayout_2.addLayout(self.formLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.edit_selected_btn = QtWidgets.QPushButton(GameList)
        self.edit_selected_btn.setObjectName("edit_selected_btn")
        self.horizontalLayout_3.addWidget(self.edit_selected_btn)
        self.horizontalLayout_3.setStretch(0, 1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4.addLayout(self.verticalLayout_2)
        self.horizontalLayout_4.setStretch(0, 2)
        self.horizontalLayout_4.setStretch(1, 6)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.retranslateUi(GameList)
        QtCore.QMetaObject.connectSlotsByName(GameList)

    def retranslateUi(self, GameList):
        _translate = QtCore.QCoreApplication.translate
        GameList.setWindowTitle(_translate("GameList", "Form"))
        self.game_list_filter.setPlaceholderText(_translate("GameList", "Search by game name..."))
        self.create_new_btn.setText(_translate("GameList", "New"))
        self.dupe_selected_btn.setText(_translate("GameList", "Dupe"))
        self.delete_selected_btn.setText(_translate("GameList", "Delete"))
        self.label.setText(_translate("GameList", "Name:"))
        self.name.setPlaceholderText(_translate("GameList", "Dark Souls Remastered"))
        self.label_2.setText(_translate("GameList", "Save File Name:"))
        self.file_name.setPlaceholderText(_translate("GameList", "DRAKS0005.sl2"))
        self.label_3.setText(_translate("GameList", "Game.exe Name"))
        self.exe_name.setPlaceholderText(_translate("GameList", "DarkSoulsRemastered.exe"))
        self.label_4.setText(_translate("GameList", "Save File Path:"))
        self.save_file_path.setPlaceholderText(_translate("GameList", "#Documents#\\NBGI\\DARK SOULS REMASTERED\\#ID#"))
        self.save_file_path_btn.setText(_translate("GameList", "..."))
        self.label_5.setText(_translate("GameList", "Backup Path:"))
        self.backup_path.setPlaceholderText(_translate("GameList", "PYAB\\Backups\\GameName\\ProfileName\\backup.zip"))
        self.backup_path_btn.setText(_translate("GameList", "..."))
        self.label_7.setText(_translate("GameList", "Icon:"))
        self.label_6.setText(_translate("GameList", "Note:"))
        self.label_9.setText(_translate("GameList", "Watch File:"))
        self.edit_selected_btn.setText(_translate("GameList", "Edit Selected"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    GameList = QtWidgets.QWidget()
    ui = Ui_GameList()
    ui.setupUi(GameList)
    GameList.show()
    sys.exit(app.exec())
