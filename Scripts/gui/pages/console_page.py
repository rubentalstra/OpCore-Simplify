"""Console log page - elevated qfluentwidgets experience"""

import re
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QCursor
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
    TextEdit,
    FluentIcon,
    ScrollArea,
    CommandBar,
    Action,
    RoundMenu,
    SettingCardGroup,
    SwitchSettingCard,
)

from ..styles import COLORS, SPACING, RADIUS


class ConsolePage(ScrollArea):
    """Console log viewer with rich filtering and controls"""

    LEVELS = ("All", "Info", "Warning", "Error", "Debug")

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("consolePage")
        self.controller = parent
        
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)

        self._log_entries: list[tuple[str, str]] = []
        self._auto_scroll_enabled = True
        self._last_update_text = "--"

        self.setup_ui()
        self._apply_filters()

    def setup_ui(self):
        # Configure scroll area
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()
        
        # Set layout spacing and margins
        layout = self.expandLayout
        layout.setContentsMargins(
            SPACING['xxlarge'],
            SPACING['xlarge'],
            SPACING['xxlarge'],
            SPACING['xlarge'],
        )
        layout.setSpacing(SPACING['large'])

        # Page header
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(SPACING['tiny'])

        title_label = SubtitleLabel("Console Log")
        header_layout.addWidget(title_label)

        subtitle_label = BodyLabel("Real-time application logs and events")
        subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_container)

        # Filter controls using SettingCardGroup (qfluentwidgets best practice)
        filter_group = SettingCardGroup("Filter and Display Options", self.scrollWidget)
        
        # Level filter card
        level_card = CardWidget()
        level_layout = QHBoxLayout(level_card)
        level_layout.setContentsMargins(SPACING['large'], SPACING['medium'], SPACING['large'], SPACING['medium'])
        
        level_label_container = QVBoxLayout()
        level_label_container.setSpacing(SPACING['tiny'])
        level_title = StrongBodyLabel("Log Level Filter")
        level_desc = BodyLabel("Filter logs by severity level")
        level_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        level_label_container.addWidget(level_title)
        level_label_container.addWidget(level_desc)
        
        level_layout.addLayout(level_label_container)
        level_layout.addStretch()
        
        self.level_filter = ComboBox()
        self.level_filter.addItems(self.LEVELS)
        self.level_filter.currentTextChanged.connect(self._apply_filters)
        self.level_filter.setMinimumWidth(140)
        level_layout.addWidget(self.level_filter)
        
        filter_group.addSettingCard(level_card)
        
        # Search filter card
        search_card = CardWidget()
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(SPACING['large'], SPACING['medium'], SPACING['large'], SPACING['medium'])
        
        search_label_container = QVBoxLayout()
        search_label_container.setSpacing(SPACING['tiny'])
        search_title = StrongBodyLabel("Search Logs")
        search_desc = BodyLabel("Search for specific text in log messages")
        search_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        search_label_container.addWidget(search_title)
        search_label_container.addWidget(search_desc)
        
        search_layout.addLayout(search_label_container)
        search_layout.addStretch()
        
        self.search_input = LineEdit()
        self.search_input.setPlaceholderText("Search in logs...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filters)
        self.search_input.setMinimumWidth(250)
        search_layout.addWidget(self.search_input)
        
        filter_group.addSettingCard(search_card)
        
        # Quick filter card
        quick_filter_card = CardWidget()
        quick_filter_layout = QHBoxLayout(quick_filter_card)
        quick_filter_layout.setContentsMargins(SPACING['large'], SPACING['medium'], SPACING['large'], SPACING['medium'])
        
        quick_label_container = QVBoxLayout()
        quick_label_container.setSpacing(SPACING['tiny'])
        quick_title = StrongBodyLabel("Quick Filters")
        quick_desc = BodyLabel("Apply preset filters for common scenarios")
        quick_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        quick_label_container.addWidget(quick_title)
        quick_label_container.addWidget(quick_desc)
        
        quick_filter_layout.addLayout(quick_label_container)
        quick_filter_layout.addStretch()
        
        self.quick_filter_btn = PushButton(FluentIcon.FILTER, "Show Presets")
        self.quick_filter_btn.clicked.connect(self._show_quick_filter_menu)
        quick_filter_layout.addWidget(self.quick_filter_btn)
        
        filter_group.addSettingCard(quick_filter_card)
        
        # Auto-scroll setting card
        self.auto_scroll_card = SwitchSettingCard(
            FluentIcon.DOWN,
            "Auto-scroll",
            "Automatically scroll to newest entries when new logs arrive",
            parent=self.scrollWidget
        )
        self.auto_scroll_card.switchButton.setChecked(True)
        self.auto_scroll_card.switchButton.checkedChanged.connect(self._toggle_auto_scroll)
        filter_group.addSettingCard(self.auto_scroll_card)
        
        # Word wrap setting card
        self.wrap_card = SwitchSettingCard(
            FluentIcon.ALIGNMENT,
            "Word Wrap",
            "Wrap long lines for better readability",
            parent=self.scrollWidget
        )
        self.wrap_card.switchButton.setChecked(True)
        self.wrap_card.switchButton.checkedChanged.connect(self._toggle_wrap_mode)
        filter_group.addSettingCard(self.wrap_card)
        
        layout.addWidget(filter_group)
        
        # Filter status info
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(SPACING['large'], SPACING['small'], SPACING['large'], SPACING['small'])
        
        self.filter_status_label = BodyLabel("Showing all logs")
        self.filter_status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        status_layout.addWidget(self.filter_status_label)
        status_layout.addStretch()
        
        layout.addWidget(status_container)

        # Console output card
        console_card = CardWidget()
        console_layout = QVBoxLayout(console_card)
        console_layout.setContentsMargins(
            SPACING['large'],
            SPACING['large'],
            SPACING['large'],
            SPACING['large'],
        )
        console_layout.setSpacing(SPACING['medium'])

        # Console header with CommandBar
        console_header = QHBoxLayout()
        console_title = StrongBodyLabel("Console Output")
        console_header.addWidget(console_title)
        console_header.addStretch()

        # Create CommandBar with actions
        self.command_bar = CommandBar(self.scrollWidget)
        
        # Clear action
        clear_action = Action(FluentIcon.DELETE, "Clear")
        clear_action.triggered.connect(self.clear_console)
        clear_action.setToolTip("Clear all console logs")
        self.command_bar.addAction(clear_action)
        
        # Copy action
        copy_action = Action(FluentIcon.COPY, "Copy")
        copy_action.triggered.connect(self.copy_console)
        copy_action.setToolTip("Copy visible logs to clipboard")
        self.command_bar.addAction(copy_action)
        
        # Export action (primary)
        export_action = Action(FluentIcon.SAVE, "Export")
        export_action.triggered.connect(self.save_console)
        export_action.setToolTip("Export logs to file")
        self.command_bar.addAction(export_action)
        
        self.command_bar.addSeparator()
        
        # Jump to bottom action
        jump_action = Action(FluentIcon.DOWN, "Jump to Bottom")
        jump_action.triggered.connect(self.scroll_to_bottom)
        jump_action.setToolTip("Scroll to the bottom of the console")
        self.command_bar.addAction(jump_action)
        
        # More options menu
        self.command_bar.addSeparator()
        more_action = Action(FluentIcon.MORE, "More")
        more_action.triggered.connect(self._show_more_menu)
        more_action.setToolTip("Additional options")
        self.command_bar.addAction(more_action)
        
        console_header.addWidget(self.command_bar)
        console_layout.addLayout(console_header)

        # Console text area
        self.console_text = TextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setPlaceholderText(
            "Console logs will appear here...\n\n"
            "Waiting for application events..."
        )
        self.console_text.setMinimumHeight(450)
        self.console_text.setStyleSheet(
            f"background: {COLORS['bg_secondary']};"
            f"border: 1px solid {COLORS['border_light']};"
            f"border-radius: {RADIUS['card']}px;"
            "font-family: 'Consolas', 'Monaco', 'Courier New', monospace;"
            "font-size: 13px;"
            "padding: 8px;"
        )
        console_layout.addWidget(self.console_text)

        layout.addWidget(console_card)
        layout.addStretch()

    def _apply_filters(self):
        """Apply current filter settings to log entries"""
        level = self.level_filter.currentText() if hasattr(self, 'level_filter') else self.LEVELS[0]
        query = self.search_input.text().strip().lower() if hasattr(self, 'search_input') else ""

        filtered: list[str] = []
        for entry_level, entry_text in self._log_entries:
            if level != "All" and entry_level.lower() != level.lower():
                continue
            if query and query not in entry_text.lower():
                continue
            filtered.append(entry_text)

        if filtered:
            self.console_text.setPlainText("\n".join(filtered))
        else:
            placeholder = "No logs match the current filters." if self._log_entries else "Console logs will appear here...\n\nWaiting for application events..."
            self.console_text.setPlainText(placeholder)

        if self._auto_scroll_enabled and filtered:
            self.scroll_to_bottom()

        self._update_metrics(len(filtered), level)

    def _update_metrics(self, visible_count: int, level: str):
        """Update the filter status display"""
        # Update filter status label with detailed information
        if len(self._log_entries) == 0:
            status_text = "No logs yet"
        elif visible_count == len(self._log_entries):
            status_text = f"Showing all {visible_count} log(s)"
        else:
            status_text = f"Showing {visible_count} of {len(self._log_entries)} log(s)"
        
        if level != "All":
            status_text += f" · Filter: {level}"
        
        search_query = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        if search_query:
            status_text += f" · Search: '{search_query}'"
            
        self.filter_status_label.setText(status_text)

    def _toggle_auto_scroll(self, checked: bool):
        self._auto_scroll_enabled = checked

    def _toggle_wrap_mode(self, checked: bool):
        mode = (
            QTextEdit.LineWrapMode.WidgetWidth
            if checked
            else QTextEdit.LineWrapMode.NoWrap
        )
        self.console_text.setLineWrapMode(mode)

    def append_log(self, message: str, level: str = "Info"):
        normalized_level = level.capitalize() if level else "Info"
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{normalized_level.upper()}] {message}"
        self._log_entries.append((normalized_level, formatted))
        self._last_update_text = timestamp
        self._apply_filters()

    def clear_console(self):
        self._log_entries.clear()
        self._last_update_text = "--"
        self._apply_filters()

    def copy_console(self):
        QApplication.clipboard().setText(self.console_text.toPlainText())
        self.controller.update_status("Console log copied", 'success')

    def save_console(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Console Log",
            "console.log",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.console_text.toPlainText())
                self.controller.update_status("Console log saved successfully", 'success')
            except Exception as exc:  # pragma: no cover - surfaced via status chip
                self.controller.update_status(f"Failed to save log: {exc}", 'error')

    def scroll_to_bottom(self):
        scroll_bar = self.console_text.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
    
    def _show_more_menu(self):
        """Show a menu with additional console options"""
        menu = RoundMenu(parent=self.scrollWidget)
        
        # Select all action
        select_all_action = Action(FluentIcon.SELECT_ALL, "Select All")
        select_all_action.triggered.connect(self.console_text.selectAll)
        menu.addAction(select_all_action)
        
        menu.addSeparator()
        
        # Font size actions
        font_menu = RoundMenu("Font Size", self.scrollWidget)
        font_menu.setIcon(FluentIcon.FONT)
        
        small_font_action = Action(FluentIcon.FONT, "Small (11px)")
        small_font_action.triggered.connect(lambda: self._set_font_size(11))
        font_menu.addAction(small_font_action)
        
        medium_font_action = Action(FluentIcon.FONT, "Medium (13px)")
        medium_font_action.triggered.connect(lambda: self._set_font_size(13))
        font_menu.addAction(medium_font_action)
        
        large_font_action = Action(FluentIcon.FONT, "Large (15px)")
        large_font_action.triggered.connect(lambda: self._set_font_size(15))
        font_menu.addAction(large_font_action)
        
        menu.addMenu(font_menu)
        
        menu.addSeparator()
        
        # Clear filters action
        clear_filters_action = Action(FluentIcon.CANCEL, "Clear All Filters")
        clear_filters_action.triggered.connect(self._clear_all_filters)
        menu.addAction(clear_filters_action)
        
        # Show menu at cursor position
        menu.exec(QCursor.pos())
    
    def _set_font_size(self, size: int):
        """Set the console text font size"""
        current_style = self.console_text.styleSheet()
        # Replace font-size in stylesheet
        new_style = re.sub(r'font-size:\s*\d+px;', f'font-size: {size}px;', current_style)
        self.console_text.setStyleSheet(new_style)
        self.controller.update_status(f"Console font size set to {size}px", 'success')
    
    def _clear_all_filters(self):
        """Clear all active filters"""
        self.level_filter.setCurrentText("All")
        self.search_input.clear()
        self.controller.update_status("All filters cleared", 'success')
    
    def _show_quick_filter_menu(self):
        """Show quick filter menu with preset filters"""
        menu = RoundMenu(parent=self.scrollWidget)
        
        # Show only errors
        errors_action = Action(FluentIcon.CANCEL, "Show Only Errors")
        errors_action.triggered.connect(lambda: self._quick_filter("Error"))
        menu.addAction(errors_action)
        
        # Show only warnings
        warnings_action = Action(FluentIcon.WARNING, "Show Only Warnings")
        warnings_action.triggered.connect(lambda: self._quick_filter("Warning"))
        menu.addAction(warnings_action)
        
        # Show only info
        info_action = Action(FluentIcon.INFO, "Show Only Info")
        info_action.triggered.connect(lambda: self._quick_filter("Info"))
        menu.addAction(info_action)
        
        menu.addSeparator()
        
        # Clear all filters
        clear_action = Action(FluentIcon.ACCEPT, "Show All Levels")
        clear_action.triggered.connect(self._clear_all_filters)
        menu.addAction(clear_action)
        
        # Show menu at cursor position
        menu.exec(QCursor.pos())
    
    def _quick_filter(self, level: str):
        """Apply a quick filter"""
        self.level_filter.setCurrentText(level)
        self.controller.update_status(f"Filter applied - showing only {level}", 'info')

    def refresh(self):
        """Allow parent controller to request a soft refresh."""
        self._apply_filters()
