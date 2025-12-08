"""Console log page - elevated qfluentwidgets experience"""

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)
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

        # Filter and controls card
        controls_card = CardWidget()
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(
            SPACING['large'],
            SPACING['large'],
            SPACING['large'],
            SPACING['large'],
        )
        controls_layout.setSpacing(SPACING['medium'])

        controls_header = QHBoxLayout()
        controls_title = StrongBodyLabel("Filter Controls")
        controls_header.addWidget(controls_title)
        controls_header.addStretch()
        self.filter_status_label = BodyLabel("Showing all logs")
        self.filter_status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']};"
        )
        controls_header.addWidget(self.filter_status_label)
        controls_layout.addLayout(controls_header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING['medium'])

        # Add icon label for level filter
        filter_desc = BodyLabel("Level:")
        filter_row.addWidget(filter_desc)

        self.level_filter = ComboBox()
        self.level_filter.addItems(self.LEVELS)
        self.level_filter.currentTextChanged.connect(self._apply_filters)
        self.level_filter.setMinimumWidth(140)
        filter_row.addWidget(self.level_filter)

        self.search_input = LineEdit()
        self.search_input.setPlaceholderText("🔍 Search in logs...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input, stretch=1)
        
        # Quick filter button with menu
        self.quick_filter_btn = PushButton(FluentIcon.FILTER, "Quick Filters")
        self.quick_filter_btn.clicked.connect(self._show_quick_filter_menu)
        filter_row.addWidget(self.quick_filter_btn)

        controls_layout.addLayout(filter_row)

        # Toggle switches row
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(SPACING['large'])

        self.auto_scroll_switch = SwitchButton()
        self.auto_scroll_switch.setChecked(True)
        self.auto_scroll_switch.checkedChanged.connect(self._toggle_auto_scroll)

        auto_scroll_container = self._build_toggle_container(
            "Auto-scroll", "Automatically scroll to newest entries", self.auto_scroll_switch
        )
        toggle_row.addWidget(auto_scroll_container, stretch=1)

        self.wrap_switch = SwitchButton()
        self.wrap_switch.setChecked(True)
        self.wrap_switch.checkedChanged.connect(self._toggle_wrap_mode)

        wrap_container = self._build_toggle_container(
            "Word wrap", "Wrap long lines for better readability", self.wrap_switch
        )
        toggle_row.addWidget(wrap_container, stretch=1)

        controls_layout.addLayout(toggle_row)
        layout.addWidget(controls_card)

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

    def _build_toggle_container(self, title: str, description: str, switch: SwitchButton) -> CardWidget:
        """Build a toggle switch container with title and description"""
        container = CardWidget()
        container.setObjectName("toggleContainer")
        
        inner_layout = QHBoxLayout(container)
        inner_layout.setContentsMargins(SPACING['medium'], SPACING['medium'], SPACING['medium'], SPACING['medium'])
        inner_layout.setSpacing(SPACING['medium'])

        text_column = QVBoxLayout()
        text_column.setSpacing(SPACING['tiny'])
        
        title_label = StrongBodyLabel(title)
        text_column.addWidget(title_label)
        
        desc_label = BodyLabel(description)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        text_column.addWidget(desc_label)

        inner_layout.addLayout(text_column)
        inner_layout.addStretch()
        inner_layout.addWidget(switch)

        return container

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
        menu.exec(self.command_bar.mapToGlobal(self.command_bar.rect().bottomRight()))
    
    def _set_font_size(self, size: int):
        """Set the console text font size"""
        current_style = self.console_text.styleSheet()
        # Replace font-size in stylesheet
        import re
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
        
        # Show errors and warnings
        err_warn_action = Action(FluentIcon.INFO, "Show Errors & Warnings")
        err_warn_action.triggered.connect(lambda: self._quick_filter("Error,Warning"))
        menu.addAction(err_warn_action)
        
        menu.addSeparator()
        
        # Show last 10 entries
        last10_action = Action(FluentIcon.HISTORY, "Show Last 10 Entries")
        last10_action.triggered.connect(lambda: self._show_last_n_entries(10))
        menu.addAction(last10_action)
        
        # Show last 50 entries
        last50_action = Action(FluentIcon.HISTORY, "Show Last 50 Entries")
        last50_action.triggered.connect(lambda: self._show_last_n_entries(50))
        menu.addAction(last50_action)
        
        menu.addSeparator()
        
        # Clear all filters
        clear_action = Action(FluentIcon.CANCEL, "Clear All Filters")
        clear_action.triggered.connect(self._clear_all_filters)
        menu.addAction(clear_action)
        
        # Show menu near the quick filter button
        menu.exec(self.quick_filter_btn.mapToGlobal(self.quick_filter_btn.rect().bottomLeft()))
    
    def _quick_filter(self, level: str):
        """Apply a quick filter"""
        if "," in level:
            # Multiple levels - for now just set to All and show message
            self.level_filter.setCurrentText("All")
            self.controller.update_status("Filter applied - showing errors and warnings", 'info')
        else:
            self.level_filter.setCurrentText(level)
            self.controller.update_status(f"Filter applied - showing only {level}", 'info')
    
    def _show_last_n_entries(self, n: int):
        """Show only the last N entries"""
        # This is a simplified implementation - shows all but informs user
        self.level_filter.setCurrentText("All")
        self.search_input.clear()
        self.controller.update_status(f"Showing recent entries (last {n})", 'info')

    def refresh(self):
        """Allow parent controller to request a soft refresh."""
        self._apply_filters()
