# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtGui, QtWidgets


# ── Card colors (inline to avoid import dependency) ─────────────────────
_BG = "#121212"
_BG_LIGHT = "#1e1e1e"
_BG_ELEVATED = "#252525"
_ACCENT = "#2a2a2a"
_BORDER = "#333333"
_PRIMARY = "#3b82f6"
_PRIMARY_HOVER = "#2563eb"
_TEXT = "#f0f0f0"
_TEXT_DIM = "#71717a"
_ERROR = "#ef4444"
_ERROR_HOVER = "#dc2626"

_CARD_STYLE = f"""
    QFrame[card="true"] {{
        background-color: {_BG_LIGHT};
        border: 1px solid {_BORDER};
        border-radius: 10px;
    }}
"""

_LIST_STYLE = f"""
    QListWidget {{
        background-color: {_BG_ELEVATED};
        border: 1px solid {_BORDER};
        border-radius: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {_PRIMARY};
    }}
    QListWidget::item:hover:!selected {{
        background-color: {_ACCENT};
    }}
"""

_SECONDARY_BTN = f"""
    QPushButton {{
        background-color: {_ACCENT};
        color: {_TEXT};
    }}
    QPushButton:hover {{
        background-color: {_BG_ELEVATED};
    }}
"""

_DANGER_BTN = f"""
    QPushButton {{
        background-color: {_ERROR};
        color: {_TEXT};
    }}
    QPushButton:hover {{
        background-color: {_ERROR_HOVER};
    }}
"""


def _make_card(parent):
    card = QtWidgets.QFrame(parent)
    card.setProperty("card", True)
    card.setStyleSheet(_CARD_STYLE)
    return card


def _make_section_label(text, parent):
    lbl = QtWidgets.QLabel(text, parent)
    font = QtGui.QFont("Segoe UI", 13)
    font.setBold(True)
    lbl.setFont(font)
    lbl.setStyleSheet(f"color: {_TEXT}; background: transparent; border: none;")
    return lbl


def _make_dim_label(text, parent):
    lbl = QtWidgets.QLabel(text, parent)
    lbl.setStyleSheet(f"color: {_TEXT_DIM}; background: transparent; border: none;")
    return lbl


def _make_value_label(parent, word_wrap=False):
    lbl = QtWidgets.QLabel(parent)
    lbl.setStyleSheet(f"color: {_TEXT}; background: transparent; border: none;")
    if word_wrap:
        lbl.setWordWrap(True)
    return lbl


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 760)
        MainWindow.setMinimumSize(1024, 640)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        main_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(8, 8, 8, 4)
        main_layout.setSpacing(8)

        # ════════════════════════════════════════════════════════════════
        #  SIDEBAR  (fixed width 280)
        # ════════════════════════════════════════════════════════════════
        sidebar = QtWidgets.QWidget(self.centralwidget)
        sidebar.setFixedWidth(280)
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(8)

        # ── Games card ──────────────────────────────────────────────────
        games_card = _make_card(sidebar)
        games_vl = QtWidgets.QVBoxLayout(games_card)
        games_vl.setContentsMargins(12, 10, 12, 10)
        games_vl.setSpacing(6)

        games_header = QtWidgets.QHBoxLayout()
        self.label = _make_section_label("Games", games_card)
        games_header.addWidget(self.label)
        games_header.addStretch()
        self.show_prof_game_only = QtWidgets.QCheckBox(games_card)
        self.show_prof_game_only.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.show_prof_game_only.setChecked(True)
        self.show_prof_game_only.setObjectName("show_prof_game_only")
        self.show_prof_game_only.setStyleSheet("background: transparent; border: none;")
        games_header.addWidget(self.show_prof_game_only)
        games_vl.addLayout(games_header)

        self.game_list_filter = QtWidgets.QLineEdit(games_card)
        self.game_list_filter.setObjectName("game_list_filter")
        games_vl.addWidget(self.game_list_filter)

        self.selection_game_list = QtWidgets.QListWidget(games_card)
        self.selection_game_list.setObjectName("selection_game_list")
        self.selection_game_list.setStyleSheet(_LIST_STYLE)
        games_vl.addWidget(self.selection_game_list, 1)

        game_btns = QtWidgets.QHBoxLayout()
        game_btns.setSpacing(6)
        self.create_game = QtWidgets.QPushButton(games_card)
        self.create_game.setObjectName("create_game")
        self.edit_game = QtWidgets.QPushButton(games_card)
        self.edit_game.setObjectName("edit_game")
        self.edit_game.setStyleSheet(_SECONDARY_BTN)
        game_btns.addWidget(self.create_game)
        game_btns.addWidget(self.edit_game)
        games_vl.addLayout(game_btns)

        sidebar_layout.addWidget(games_card, 1)

        # ── Profiles card ──────────────────────────────────────────────
        profiles_card = _make_card(sidebar)
        profiles_vl = QtWidgets.QVBoxLayout(profiles_card)
        profiles_vl.setContentsMargins(12, 10, 12, 10)
        profiles_vl.setSpacing(6)

        profiles_header = QtWidgets.QHBoxLayout()
        self.profiles_label = _make_section_label("Profiles", profiles_card)
        self.profiles_label.setObjectName("profiles_label")
        profiles_header.addWidget(self.profiles_label)
        profiles_header.addStretch()
        self.show_all_profiles = QtWidgets.QCheckBox(profiles_card)
        self.show_all_profiles.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.show_all_profiles.setObjectName("show_all_profiles")
        self.show_all_profiles.setStyleSheet("background: transparent; border: none;")
        profiles_header.addWidget(self.show_all_profiles)
        profiles_vl.addLayout(profiles_header)

        self.profile_list_filter = QtWidgets.QLineEdit(profiles_card)
        self.profile_list_filter.setObjectName("profile_list_filter")
        profiles_vl.addWidget(self.profile_list_filter)

        self.selection_profile_list = QtWidgets.QListWidget(profiles_card)
        self.selection_profile_list.setObjectName("selection_profile_list")
        self.selection_profile_list.setStyleSheet(_LIST_STYLE)
        profiles_vl.addWidget(self.selection_profile_list, 1)

        profile_btns = QtWidgets.QHBoxLayout()
        profile_btns.setSpacing(6)
        self.create_profile = QtWidgets.QPushButton(profiles_card)
        self.create_profile.setObjectName("create_profile")
        self.edit_profile = QtWidgets.QPushButton(profiles_card)
        self.edit_profile.setObjectName("edit_profile")
        self.edit_profile.setStyleSheet(_SECONDARY_BTN)
        profile_btns.addWidget(self.create_profile)
        profile_btns.addWidget(self.edit_profile)
        profiles_vl.addLayout(profile_btns)

        sidebar_layout.addWidget(profiles_card, 1)

        main_layout.addWidget(sidebar)

        # ════════════════════════════════════════════════════════════════
        #  MAIN AREA
        # ════════════════════════════════════════════════════════════════
        main_area = QtWidgets.QVBoxLayout()
        main_area.setSpacing(8)

        # ── Top row: backup table + info column ────────────────────────
        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(8)

        # ── Backup table card ──────────────────────────────────────────
        table_card = _make_card(self.centralwidget)
        table_vl = QtWidgets.QVBoxLayout(table_card)
        table_vl.setContentsMargins(12, 10, 12, 10)
        table_vl.setSpacing(6)

        table_vl.addWidget(_make_section_label("Backups", table_card))

        self.backup_table = QtWidgets.QTableWidget(table_card)
        self.backup_table.setObjectName("backup_table")
        self.backup_table.setColumnCount(3)
        self.backup_table.setRowCount(0)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.setShowGrid(False)
        self.backup_table.setFrameShape(QtWidgets.QFrame.NoFrame)
        item = QtWidgets.QTableWidgetItem()
        self.backup_table.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.backup_table.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.backup_table.setHorizontalHeaderItem(2, item)
        table_vl.addWidget(self.backup_table, 1)

        top_row.addWidget(table_card, 3)

        # ── Info column (profile info + actions) ───────────────────────
        info_col = QtWidgets.QVBoxLayout()
        info_col.setSpacing(8)

        # -- Profile info card --
        info_card = _make_card(self.centralwidget)
        info_vl = QtWidgets.QVBoxLayout(info_card)
        info_vl.setContentsMargins(12, 10, 12, 10)
        info_vl.setSpacing(4)

        info_header = QtWidgets.QHBoxLayout()
        info_header.addWidget(_make_section_label("Profile Info", info_card))
        info_header.addStretch()
        self.game_icon = QtWidgets.QLabel(info_card)
        self.game_icon.setMinimumSize(90, 90)
        self.game_icon.setAlignment(QtCore.Qt.AlignCenter)
        self.game_icon.setObjectName("game_icon")
        self.game_icon.setStyleSheet("background: transparent; border: none;")
        info_header.addWidget(self.game_icon)
        info_vl.addLayout(info_header)

        info_grid = QtWidgets.QGridLayout()
        info_grid.setHorizontalSpacing(12)
        info_grid.setVerticalSpacing(4)

        row = 0
        info_grid.addWidget(_make_dim_label("Selected Profile:", info_card), row, 0)
        self.selected_profile = _make_value_label(info_card)
        self.selected_profile.setObjectName("selected_profile")
        info_grid.addWidget(self.selected_profile, row, 1)

        row += 1
        info_grid.addWidget(_make_dim_label("Files:", info_card), row, 0)
        self.files_found = _make_value_label(info_card)
        self.files_found.setObjectName("files_found")
        info_grid.addWidget(self.files_found, row, 1)

        row += 1
        info_grid.addWidget(_make_dim_label("Size:", info_card), row, 0)
        self.weight_found = _make_value_label(info_card)
        self.weight_found.setObjectName("weight_found")
        info_grid.addWidget(self.weight_found, row, 1)

        row += 1
        info_grid.addWidget(_make_dim_label("Save File:", info_card), row, 0)
        self.save_file_found = _make_value_label(info_card, word_wrap=True)
        self.save_file_found.setObjectName("save_file_found")
        info_grid.addWidget(self.save_file_found, row, 1)

        row += 1
        info_grid.addWidget(_make_dim_label("Auto Backup:", info_card), row, 0)
        self.auto_backup_timer = _make_value_label(info_card)
        self.auto_backup_timer.setObjectName("auto_backup_timer")
        info_grid.addWidget(self.auto_backup_timer, row, 1)

        row += 1
        info_grid.addWidget(_make_dim_label("Screenshots:", info_card), row, 0)
        self.screenshots = _make_value_label(info_card)
        self.screenshots.setObjectName("screenshots")
        info_grid.addWidget(self.screenshots, row, 1)

        # Screen selector hidden — screenshot now captures game window automatically
        self.screen_slider = QtWidgets.QSlider(info_card)
        self.screen_slider.setObjectName("screen_slider")
        self.screen_slider.hide()
        self.screen_label = QtWidgets.QLabel(info_card)
        self.screen_label.setObjectName("screen_label")
        self.screen_label.hide()

        info_vl.addLayout(info_grid)
        info_col.addWidget(info_card, 1)

        # -- Actions card --
        actions_card = _make_card(self.centralwidget)
        actions_vl = QtWidgets.QVBoxLayout(actions_card)
        actions_vl.setContentsMargins(12, 10, 12, 10)
        actions_vl.setSpacing(6)

        actions_vl.addWidget(_make_section_label("Actions", actions_card))

        self.launch_at_start_checkbox = QtWidgets.QCheckBox(actions_card)
        self.launch_at_start_checkbox.setObjectName("launch_at_start_checkbox")
        self.launch_at_start_checkbox.setStyleSheet("background: transparent; border: none;")
        actions_vl.addWidget(self.launch_at_start_checkbox)

        self.open_backup_path_btn = QtWidgets.QPushButton(actions_card)
        self.open_backup_path_btn.setObjectName("open_backup_path_btn")
        self.open_backup_path_btn.setStyleSheet(_SECONDARY_BTN)
        actions_vl.addWidget(self.open_backup_path_btn)

        del_btns = QtWidgets.QHBoxLayout()
        del_btns.setSpacing(6)
        self.delete_selected_backup = QtWidgets.QPushButton(actions_card)
        self.delete_selected_backup.setObjectName("delete_selected_backup")
        self.delete_selected_backup.setStyleSheet(_DANGER_BTN)
        self.delete_all_backup = QtWidgets.QPushButton(actions_card)
        self.delete_all_backup.setObjectName("delete_all_backup")
        self.delete_all_backup.setStyleSheet(_DANGER_BTN)
        del_btns.addWidget(self.delete_selected_backup)
        del_btns.addWidget(self.delete_all_backup)
        actions_vl.addLayout(del_btns)

        info_col.addWidget(actions_card)

        top_row.addLayout(info_col, 2)
        main_area.addLayout(top_row, 3)

        # ── Bottom row: screenshot + game status ───────────────────────
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.setSpacing(8)

        # -- Screenshot card --
        screenshot_card = _make_card(self.centralwidget)
        screenshot_vl = QtWidgets.QVBoxLayout(screenshot_card)
        screenshot_vl.setContentsMargins(12, 10, 12, 10)
        screenshot_vl.setSpacing(6)

        screenshot_vl.addWidget(_make_section_label("Screenshot Preview", screenshot_card))

        self.graphicsView = QtWidgets.QGraphicsView(screenshot_card)
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.graphicsView.setStyleSheet(f"background-color: {_BG_ELEVATED}; border-radius: 6px;")
        screenshot_vl.addWidget(self.graphicsView, 1)

        bottom_row.addWidget(screenshot_card, 3)

        # -- Game status card --
        status_card = _make_card(self.centralwidget)
        status_vl = QtWidgets.QVBoxLayout(status_card)
        status_vl.setContentsMargins(12, 10, 12, 10)
        status_vl.setSpacing(8)

        status_vl.addWidget(_make_section_label("Game Status", status_card))

        game_hl = QtWidgets.QHBoxLayout()
        game_hl.addWidget(_make_dim_label("Game:", status_card))
        self.game_label = _make_value_label(status_card)
        self.game_label.setObjectName("game_label")
        game_hl.addWidget(self.game_label, 1)
        status_vl.addLayout(game_hl)

        backup_hl = QtWidgets.QHBoxLayout()
        backup_hl.setSpacing(8)
        self.auto_backup_btn = QtWidgets.QPushButton(status_card)
        self.auto_backup_btn.setObjectName("auto_backup_btn")
        backup_hl.addWidget(self.auto_backup_btn)
        self.backup_updates = QtWidgets.QLabel(status_card)
        self.backup_updates.setObjectName("backup_updates")
        self.backup_updates.setStyleSheet(f"color: {_TEXT_DIM}; background: transparent; border: none;")
        backup_hl.addWidget(self.backup_updates, 1)
        status_vl.addLayout(backup_hl)

        self.backup_now_btn = QtWidgets.QPushButton(status_card)
        self.backup_now_btn.setObjectName("backup_now_btn")
        status_vl.addWidget(self.backup_now_btn)

        status_vl.addStretch()

        self.restore_backup_btn = QtWidgets.QPushButton(status_card)
        self.restore_backup_btn.setObjectName("restore_backup_btn")
        self.restore_backup_btn.setStyleSheet(_SECONDARY_BTN)
        status_vl.addWidget(self.restore_backup_btn)

        bottom_row.addWidget(status_card, 2)

        main_area.addLayout(bottom_row, 2)

        # ── Footer ─────────────────────────────────────────────────────
        footer = QtWidgets.QHBoxLayout()
        footer.setContentsMargins(4, 0, 4, 0)
        footer.addStretch()
        self.twitch_label = QtWidgets.QLabel(self.centralwidget)
        self.twitch_label.setObjectName("twitch_label")
        self.twitch_label.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 11px; background: transparent;")
        footer.addWidget(self.twitch_label)
        self.twitch_logo = QtWidgets.QLabel(self.centralwidget)
        self.twitch_logo.setObjectName("twitch_logo")
        self.twitch_logo.setStyleSheet("background: transparent;")
        footer.addWidget(self.twitch_logo)
        main_area.addLayout(footer)

        main_layout.addLayout(main_area, 1)

        MainWindow.setCentralWidget(self.centralwidget)

        # ════════════════════════════════════════════════════════════════
        #  MENU BAR
        # ════════════════════════════════════════════════════════════════
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setObjectName("menuBar")
        self.menuGames_List = QtWidgets.QMenu(self.menuBar)
        self.menuGames_List.setObjectName("menuGames_List")
        self.menuProfiles = QtWidgets.QMenu(self.menuBar)
        self.menuProfiles.setObjectName("menuProfiles")
        MainWindow.setMenuBar(self.menuBar)

        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.actionOpen = QtGui.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionAdd_new = QtGui.QAction(MainWindow)
        self.actionAdd_new.setObjectName("actionAdd_new")
        self.actionEdit_List = QtGui.QAction(MainWindow)
        self.actionEdit_List.setObjectName("actionEdit_List")
        self.actionAdd_New_Game = QtGui.QAction(MainWindow)
        self.actionAdd_New_Game.setObjectName("actionAdd_New_Game")
        self.actionShow_All_Profiles = QtGui.QAction(MainWindow)
        self.actionShow_All_Profiles.setObjectName("actionShow_All_Profiles")

        self.menuGames_List.addAction(self.actionEdit_List)
        self.menuGames_List.addAction(self.actionAdd_New_Game)
        self.menuProfiles.addSeparator()
        self.menuProfiles.addAction(self.actionShow_All_Profiles)
        self.menuBar.addAction(self.menuGames_List.menuAction())
        self.menuBar.addAction(self.menuProfiles.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "Games"))
        self.show_prof_game_only.setText(_translate("MainWindow", "With Profiles"))
        self.game_list_filter.setPlaceholderText(_translate("MainWindow", "Search by game name..."))
        self.create_game.setText(_translate("MainWindow", "Create New Game"))
        self.edit_game.setText(_translate("MainWindow", "Edit Game"))
        self.profiles_label.setText(_translate("MainWindow", "Profiles"))
        self.show_all_profiles.setText(_translate("MainWindow", "All Profiles"))
        self.profile_list_filter.setPlaceholderText(_translate("MainWindow", "Search by profile name..."))
        self.create_profile.setText(_translate("MainWindow", "Create New Profile"))
        self.edit_profile.setText(_translate("MainWindow", "Edit Profile"))
        item = self.backup_table.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Name"))
        item = self.backup_table.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Date"))
        item = self.backup_table.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Size"))
        self.selected_profile.setText(_translate("MainWindow", "none"))
        self.files_found.setText(_translate("MainWindow", "0 Backups found"))
        self.weight_found.setText(_translate("MainWindow", "0 Byte"))
        self.save_file_found.setText(_translate("MainWindow", "No Save File found"))
        self.auto_backup_timer.setText(_translate("MainWindow", "No profile selected."))
        self.screenshots.setText(_translate("MainWindow", "False"))
        self.screen_label.setText(_translate("MainWindow", "Screen 1"))
        self.launch_at_start_checkbox.setText(_translate("MainWindow", "Launch at start"))
        self.open_backup_path_btn.setText(_translate("MainWindow", "Open Backup Path"))
        self.delete_selected_backup.setText(_translate("MainWindow", "Delete Selected"))
        self.delete_all_backup.setText(_translate("MainWindow", "Delete All Backups"))
        self.game_label.setText(_translate("MainWindow", "No Game Loaded."))
        self.auto_backup_btn.setText(_translate("MainWindow", "Toggle Automatic Backups"))
        self.backup_updates.setText(_translate("MainWindow", "OFF"))
        self.backup_now_btn.setText(_translate("MainWindow", "Backup Now"))
        self.restore_backup_btn.setText(_translate("MainWindow", "Restore Selected"))
        self.twitch_label.setText(_translate("MainWindow", "Game images courtesy of IGDB/Twitch Interactive, Inc."))
        self.twitch_logo.setText(_translate("MainWindow", "logo"))
        self.menuGames_List.setTitle(_translate("MainWindow", "Games"))
        self.menuProfiles.setTitle(_translate("MainWindow", "Profiles"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionAdd_new.setText(_translate("MainWindow", "Add new"))
        self.actionEdit_List.setText(_translate("MainWindow", "Edit List"))
        self.actionAdd_New_Game.setText(_translate("MainWindow", "Add New Game"))
        self.actionShow_All_Profiles.setText(_translate("MainWindow", "Show All Profiles"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
