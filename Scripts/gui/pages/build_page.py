"""
Step 4: Build EFI - allows users to build their customized OpenCore EFI.
Enhanced with stunning UI/UX using qfluentwidgets components.
"""

import platform
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, CardWidget, TextEdit,
    StrongBodyLabel, ProgressBar, PrimaryPushButton, FluentIcon,
    ScrollArea, InfoBar, InfoBarPosition, TitleLabel, ProgressRing,
    TransparentToolButton, IconWidget, CaptionLabel, IndeterminateProgressRing
)

from ..styles import COLORS, SPACING, RADIUS
from ..ui_utils import build_icon_label, create_step_indicator

# Constants for build log formatting
LOG_SEPARATOR = "═" * 60
DEFAULT_LOG_TEXT = "Build log will appear here..."
MAX_ACTIVITY_LOG_ENTRIES = 50  # Maximum number of entries to keep in activity feed for performance


class BuildPage(ScrollArea):
    """Step 4: Build OpenCore EFI with enhanced UI/UX."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("buildPage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.build_in_progress = False
        self.build_successful = False
        
        # Build step tracking
        self.build_steps = []
        self.build_step_cards = []
        self.log_entries = []
        self.build_start_time = None
        self.stats_timer = None
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the build page UI with improved qfluentwidgets components."""
        # Configure scroll area
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()

        # Set layout spacing and margins
        self.expandLayout.setContentsMargins(SPACING['xxlarge'], SPACING['xlarge'],
                                             SPACING['xxlarge'], SPACING['xlarge'])
        self.expandLayout.setSpacing(SPACING['xlarge'])

        layout = self.expandLayout

        # Step indicator with title
        layout.addWidget(create_step_indicator(4))

        # Title section with better typography
        title_label = TitleLabel("Build OpenCore EFI")
        layout.addWidget(title_label)

        subtitle_label = BodyLabel("Build your customized OpenCore EFI ready for installation")
        subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle_label)

        layout.addSpacing(SPACING['medium'])

        # Build instructions card using simple CardWidget
        instructions_card = CardWidget(self.scrollWidget)
        instructions_card.setBorderRadius(RADIUS['card'])
        instructions_card_layout = QVBoxLayout(instructions_card)
        instructions_card_layout.setContentsMargins(SPACING['large'], SPACING['large'], 
                                                    SPACING['large'], SPACING['large'])
        instructions_card_layout.setSpacing(SPACING['medium'])
        
        # Card header with icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING['medium'])
        instructions_icon = build_icon_label(FluentIcon.INFO, COLORS['note_text'], size=28)
        header_layout.addWidget(instructions_icon)
        
        header_title = SubtitleLabel("Before You Build")
        header_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        instructions_card_layout.addLayout(header_layout)
        
        # Instructions content
        instructions_text = BodyLabel(
            "The build process will:\n\n"
            "• Download the latest OpenCore bootloader and required kexts\n"
            "• Apply your customized ACPI patches and configurations\n"
            "• Generate a complete EFI folder ready for installation\n\n"
            "⏱️ This process typically takes 2-5 minutes depending on your internet connection.\n"
            "📊 Progress will be shown below with real-time status updates."
        )
        instructions_text.setWordWrap(True)
        instructions_text.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.9; font-size: 14px;")
        instructions_card_layout.addWidget(instructions_text)
        
        layout.addWidget(instructions_card)

        # Build control card using simple CardWidget
        build_control_card = CardWidget(self.scrollWidget)
        build_control_card.setBorderRadius(RADIUS['card'])
        build_control_layout = QVBoxLayout(build_control_card)
        build_control_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                               SPACING['large'], SPACING['large'])
        build_control_layout.setSpacing(SPACING['large'])
        
        # Card header
        control_header_layout = QHBoxLayout()
        control_header_layout.setSpacing(SPACING['medium'])
        control_icon = build_icon_label(FluentIcon.DEVELOPER_TOOLS, COLORS['primary'], size=28)
        control_header_layout.addWidget(control_icon)
        
        control_title = SubtitleLabel("Build Control")
        control_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600;")
        control_header_layout.addWidget(control_title)
        control_header_layout.addStretch()
        build_control_layout.addLayout(control_header_layout)

        # Build button - FULL WIDTH
        self.build_btn = PrimaryPushButton(FluentIcon.DEVELOPER_TOOLS, "Build OpenCore EFI")
        self.build_btn.clicked.connect(self.start_build)
        self.build_btn.setFixedHeight(48)
        self.controller.build_btn = self.build_btn
        build_control_layout.addWidget(self.build_btn)
        
        build_hint = BodyLabel("Click to start building your customized EFI")
        build_hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        build_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        build_control_layout.addWidget(build_hint)

        # Progress section (initially hidden) - FULL WIDTH
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, SPACING['medium'], 0, 0)
        progress_layout.setSpacing(SPACING['medium'])

        # Progress status with larger, more visible icon
        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING['medium'])
        
        self.status_icon_label = QLabel()
        self.status_icon_label.setFixedSize(28, 28)
        status_row.addWidget(self.status_icon_label)
        
        self.progress_label = StrongBodyLabel("Ready to build")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 15px; font-weight: 600;")
        status_row.addWidget(self.progress_label)
        status_row.addStretch()
        
        progress_layout.addLayout(status_row)

        # Progress bar with better visibility - FULL WIDTH
        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(True)
        self.controller.progress_bar = self.progress_bar
        progress_layout.addWidget(self.progress_bar)
        
        self.controller.progress_label = self.progress_label
        self.progress_container.setVisible(False)
        
        build_control_layout.addWidget(self.progress_container)
        layout.addWidget(build_control_card)

        # Build Statistics Card (initially hidden)
        self.stats_card = CardWidget(self.scrollWidget)
        self.stats_card.setBorderRadius(RADIUS['card'])
        stats_card_layout = QVBoxLayout(self.stats_card)
        stats_card_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                             SPACING['large'], SPACING['large'])
        stats_card_layout.setSpacing(SPACING['medium'])
        
        # Stats header
        stats_header_layout = QHBoxLayout()
        stats_header_layout.setSpacing(SPACING['medium'])
        stats_icon = build_icon_label(FluentIcon.CHART, COLORS['primary'], size=28)
        stats_header_layout.addWidget(stats_icon)
        
        stats_title = SubtitleLabel("Build Statistics")
        stats_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600;")
        stats_header_layout.addWidget(stats_title)
        stats_header_layout.addStretch()
        stats_card_layout.addLayout(stats_header_layout)
        
        # Statistics grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(SPACING['large'])
        stats_grid.setContentsMargins(0, SPACING['small'], 0, 0)
        
        # Elapsed time
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setContentsMargins(SPACING['medium'], SPACING['medium'], 
                                       SPACING['medium'], SPACING['medium'])
        time_layout.setSpacing(SPACING['tiny'])
        time_icon = build_icon_label(FluentIcon.HISTORY, COLORS['info'], size=20)
        time_layout.addWidget(time_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.elapsed_time_label = SubtitleLabel("0s")
        self.elapsed_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_layout.addWidget(self.elapsed_time_label)
        time_caption = CaptionLabel("Elapsed Time")
        time_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_caption.setStyleSheet(f"color: {COLORS['text_secondary']};")
        time_layout.addWidget(time_caption)
        time_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 120, 212, 0.05);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        stats_grid.addWidget(time_widget, 0, 0)
        
        # Files downloaded
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.setContentsMargins(SPACING['medium'], SPACING['medium'], 
                                        SPACING['medium'], SPACING['medium'])
        files_layout.setSpacing(SPACING['tiny'])
        files_icon = build_icon_label(FluentIcon.DOWNLOAD, COLORS['success'], size=20)
        files_layout.addWidget(files_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.files_count_label = SubtitleLabel("0")
        self.files_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        files_layout.addWidget(self.files_count_label)
        files_caption = CaptionLabel("Files Downloaded")
        files_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        files_caption.setStyleSheet(f"color: {COLORS['text_secondary']};")
        files_layout.addWidget(files_caption)
        files_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(16, 124, 16, 0.05);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        stats_grid.addWidget(files_widget, 0, 1)
        
        # Current phase
        phase_widget = QWidget()
        phase_layout = QVBoxLayout(phase_widget)
        phase_layout.setContentsMargins(SPACING['medium'], SPACING['medium'], 
                                        SPACING['medium'], SPACING['medium'])
        phase_layout.setSpacing(SPACING['tiny'])
        phase_icon = build_icon_label(FluentIcon.TAG, COLORS['warning'], size=20)
        phase_layout.addWidget(phase_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self.current_phase_label = SubtitleLabel("Preparing")
        self.current_phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        phase_layout.addWidget(self.current_phase_label)
        phase_caption = CaptionLabel("Current Phase")
        phase_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        phase_caption.setStyleSheet(f"color: {COLORS['text_secondary']};")
        phase_layout.addWidget(phase_caption)
        phase_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 140, 0, 0.05);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        stats_grid.addWidget(phase_widget, 0, 2)
        
        stats_card_layout.addLayout(stats_grid)
        self.stats_card.setVisible(False)
        layout.addWidget(self.stats_card)

        # Live Build Activity Card (initially hidden) - ENHANCED LOG DISPLAY
        self.activity_card = CardWidget(self.scrollWidget)
        self.activity_card.setBorderRadius(RADIUS['card'])
        activity_card_layout = QVBoxLayout(self.activity_card)
        activity_card_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                                SPACING['large'], SPACING['large'])
        activity_card_layout.setSpacing(SPACING['medium'])
        
        # Activity header with toggle
        activity_header_layout = QHBoxLayout()
        activity_header_layout.setSpacing(SPACING['medium'])
        activity_icon = build_icon_label(FluentIcon.FRIGGATRISYSTEM, COLORS['primary'], size=28)
        activity_header_layout.addWidget(activity_icon)
        
        activity_title = SubtitleLabel("Live Build Activity")
        activity_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600;")
        activity_header_layout.addWidget(activity_title)
        
        # Live indicator
        self.live_indicator = QLabel()
        self.live_indicator.setText("● LIVE")
        self.live_indicator.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['error']};
                font-weight: bold;
                font-size: 11px;
                padding: 4px 8px;
                background-color: rgba(232, 17, 35, 0.1);
                border-radius: 4px;
            }}
        """)
        activity_header_layout.addWidget(self.live_indicator)
        
        activity_header_layout.addStretch()
        activity_card_layout.addLayout(activity_header_layout)
        
        activity_description = BodyLabel("Real-time updates of the build process with detailed progress information")
        activity_description.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        activity_card_layout.addWidget(activity_description)
        
        # Activity log area - scrollable container for log entries
        self.activity_log_container = QWidget()
        self.activity_log_layout = QVBoxLayout(self.activity_log_container)
        self.activity_log_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_log_layout.setSpacing(SPACING['small'])
        self.activity_log_layout.addStretch()  # Push entries to bottom
        
        # Scroll area for activity log
        activity_scroll = ScrollArea()
        activity_scroll.setWidget(self.activity_log_container)
        activity_scroll.setWidgetResizable(True)
        activity_scroll.setMinimumHeight(300)
        activity_scroll.setMaximumHeight(500)
        activity_scroll.setStyleSheet(f"""
            ScrollArea {{
                background-color: rgba(0, 0, 0, 0.02);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        activity_card_layout.addWidget(activity_scroll)
        
        self.activity_card.setVisible(False)
        layout.addWidget(self.activity_card)

        # Classic Build Log Card (collapsible, initially hidden)
        self.classic_log_card = CardWidget(self.scrollWidget)
        self.classic_log_card.setBorderRadius(RADIUS['card'])
        classic_log_layout = QVBoxLayout(self.classic_log_card)
        classic_log_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                              SPACING['large'], SPACING['large'])
        classic_log_layout.setSpacing(SPACING['medium'])
        
        # Card header with toggle button
        classic_log_header_layout = QHBoxLayout()
        classic_log_header_layout.setSpacing(SPACING['medium'])
        classic_log_icon = build_icon_label(FluentIcon.DOCUMENT, COLORS['text_secondary'], size=28)
        classic_log_header_layout.addWidget(classic_log_icon)
        
        classic_log_title = SubtitleLabel("Detailed Build Log")
        classic_log_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600;")
        classic_log_header_layout.addWidget(classic_log_title)
        
        classic_log_header_layout.addStretch()
        
        # Toggle button for collapsing/expanding
        self.toggle_log_btn = TransparentToolButton(FluentIcon.CHEVRON_DOWN)
        self.toggle_log_btn.clicked.connect(self.toggle_classic_log)
        classic_log_header_layout.addWidget(self.toggle_log_btn)
        classic_log_layout.addLayout(classic_log_header_layout)
        
        classic_log_description = BodyLabel("Technical build output with complete details (click to expand/collapse)")
        classic_log_description.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        classic_log_layout.addWidget(classic_log_description)
        
        # Build log text area - initially hidden
        self.build_log = TextEdit()
        self.build_log.setReadOnly(True)
        self.build_log.setPlainText(DEFAULT_LOG_TEXT)
        self.build_log.setMinimumHeight(300)
        self.build_log.setMaximumHeight(400)
        self.build_log.setVisible(False)  # Start collapsed
        self.build_log.setStyleSheet(f"""
            TextEdit {{
                background-color: rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: {RADIUS['small']}px;
                padding: {SPACING['large']}px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.6;
            }}
        """)
        self.controller.build_log = self.build_log
        classic_log_layout.addWidget(self.build_log)
        
        self.classic_log_card.setVisible(False)
        layout.addWidget(self.classic_log_card)

        # Success card using simple CardWidget (initially hidden)
        self.success_card = CardWidget(self.scrollWidget)
        self.success_card.setBorderRadius(RADIUS['card'])
        success_card_layout = QVBoxLayout(self.success_card)
        success_card_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                              SPACING['large'], SPACING['large'])
        success_card_layout.setSpacing(SPACING['medium'])
        
        # Success styling
        self.success_card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['success_bg']};
                border: 2px solid {COLORS['success']};
            }}
        """)
        
        # Card header
        success_header_layout = QHBoxLayout()
        success_header_layout.setSpacing(SPACING['medium'])
        success_icon = build_icon_label(FluentIcon.COMPLETED, COLORS['success'], size=32)
        success_header_layout.addWidget(success_icon)
        
        success_title = SubtitleLabel("Build Completed Successfully!")
        success_title.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
        success_header_layout.addWidget(success_title)
        success_header_layout.addStretch()
        success_card_layout.addLayout(success_header_layout)
        
        # Success content
        success_message = BodyLabel(
            "🎉 Your OpenCore EFI has been built successfully!\n\n"
            "The EFI folder is ready for installation. You can now:\n"
            "• Open the result folder to view your EFI\n"
            "• Review the post-build instructions below\n"
            "• Copy the EFI to your USB drive or EFI partition"
        )
        success_message.setWordWrap(True)
        success_message.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.9; font-size: 14px;")
        success_card_layout.addWidget(success_message)

        # Action button - FULL WIDTH
        self.open_result_btn = PrimaryPushButton(FluentIcon.FOLDER, "Open Result Folder")
        self.open_result_btn.clicked.connect(self.open_result)
        self.open_result_btn.setFixedHeight(44)
        success_card_layout.addWidget(self.open_result_btn)
        
        self.controller.open_result_btn = self.open_result_btn
        
        self.success_card.setVisible(False)
        layout.addWidget(self.success_card)

        # Post-build instructions card using simple CardWidget (initially hidden)
        self.instructions_after_build_card = CardWidget(self.scrollWidget)
        self.instructions_after_build_card.setBorderRadius(RADIUS['card'])
        instructions_after_layout = QVBoxLayout(self.instructions_after_build_card)
        instructions_after_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                                     SPACING['large'], SPACING['large'])
        instructions_after_layout.setSpacing(SPACING['medium'])
        
        # Warning styling
        self.instructions_after_build_card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['warning_bg']};
                border: 2px solid {COLORS['warning']};
            }}
        """)
        
        # Card header
        warning_header_layout = QHBoxLayout()
        warning_header_layout.setSpacing(SPACING['medium'])
        warning_icon = build_icon_label(FluentIcon.MEGAPHONE, COLORS['warning_text'], size=32)
        warning_header_layout.addWidget(warning_icon)
        
        warning_title = SubtitleLabel("Important: Before Using Your EFI")
        warning_title.setStyleSheet(f"color: {COLORS['warning_text']}; font-weight: 600;")
        warning_header_layout.addWidget(warning_title)
        warning_header_layout.addStretch()
        instructions_after_layout.addLayout(warning_header_layout)
        
        instructions_after_intro = BodyLabel(
            "Please complete these important steps before using the built EFI:"
        )
        instructions_after_intro.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        instructions_after_layout.addWidget(instructions_after_intro)
        
        # Content area for requirements (will be populated dynamically)
        self.instructions_after_content = QWidget()
        self.instructions_after_content_layout = QVBoxLayout(self.instructions_after_content)
        self.instructions_after_content_layout.setContentsMargins(0, 0, 0, 0)
        self.instructions_after_content_layout.setSpacing(SPACING['medium'])
        instructions_after_layout.addWidget(self.instructions_after_content)
        
        self.instructions_after_build_card.setVisible(False)
        layout.addWidget(self.instructions_after_build_card)

        layout.addStretch()
    
    def toggle_classic_log(self):
        """Toggle visibility of classic build log"""
        is_visible = self.build_log.isVisible()
        self.build_log.setVisible(not is_visible)
        
        # Update toggle button icon
        if is_visible:
            self.toggle_log_btn.setIcon(FluentIcon.CHEVRON_DOWN)
        else:
            self.toggle_log_btn.setIcon(FluentIcon.CHEVRON_UP)
    
    def add_log_entry(self, message, entry_type="info", icon=None):
        """
        Add a visual log entry to the activity feed.
        
        Args:
            message: Log message text
            entry_type: Type of log entry (info, success, warning, error, step)
            icon: Optional FluentIcon to use
        """
        # Create log entry widget
        entry_widget = QWidget()
        entry_layout = QHBoxLayout(entry_widget)
        entry_layout.setContentsMargins(SPACING['medium'], SPACING['small'], 
                                       SPACING['medium'], SPACING['small'])
        entry_layout.setSpacing(SPACING['medium'])
        
        # Icon based on type
        icon_map = {
            "info": (FluentIcon.INFO, COLORS['info']),
            "success": (FluentIcon.COMPLETED, COLORS['success']),
            "warning": (FluentIcon.IMPORTANT, COLORS['warning']),
            "error": (FluentIcon.CLOSE, COLORS['error']),
            "step": (FluentIcon.CHEVRON_RIGHT, COLORS['primary']),
            "download": (FluentIcon.DOWNLOAD, COLORS['primary']),
            "process": (FluentIcon.SYNC, COLORS['warning']),
        }
        
        if icon:
            icon_to_use = icon
            color = COLORS['primary']
        elif entry_type in icon_map:
            icon_to_use, color = icon_map[entry_type]
        else:
            icon_to_use, color = icon_map["info"]
        
        # Icon label
        icon_label = QLabel()
        icon_pixmap = icon_to_use.icon(color=color).pixmap(16, 16)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(20, 20)
        entry_layout.addWidget(icon_label)
        
        # Message label
        msg_label = BodyLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            BodyLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                line-height: 1.5;
            }}
        """)
        entry_layout.addWidget(msg_label, stretch=1)
        
        # Timestamp
        timestamp = CaptionLabel(datetime.now().strftime("%H:%M:%S"))
        timestamp.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        entry_layout.addWidget(timestamp)
        
        # Style based on type
        bg_colors = {
            "info": "rgba(0, 120, 212, 0.05)",
            "success": "rgba(16, 124, 16, 0.05)",
            "warning": "rgba(255, 140, 0, 0.08)",
            "error": "rgba(232, 17, 35, 0.08)",
            "step": "rgba(0, 120, 212, 0.08)",
            "download": "rgba(0, 120, 212, 0.05)",
            "process": "rgba(255, 140, 0, 0.05)",
        }
        
        bg_color = bg_colors.get(entry_type, bg_colors["info"])
        entry_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-left: 3px solid {color};
                border-radius: {RADIUS['small']}px;
            }}
        """)
        
        # Insert at the end (before stretch)
        count = self.activity_log_layout.count()
        self.activity_log_layout.insertWidget(count - 1, entry_widget)
        self.log_entries.append(entry_widget)
        
        # Limit to MAX_ACTIVITY_LOG_ENTRIES for performance
        if len(self.log_entries) > MAX_ACTIVITY_LOG_ENTRIES:
            old_entry = self.log_entries.pop(0)
            old_entry.deleteLater()
    
    def update_stats(self):
        """Update build statistics display"""
        if self.build_start_time:
            elapsed = (datetime.now() - self.build_start_time).total_seconds()
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            if mins > 0:
                self.elapsed_time_label.setText(f"{mins}m {secs}s")
            else:
                self.elapsed_time_label.setText(f"{secs}s")

    def start_build(self):
        """Start building EFI with enhanced UI feedback"""
        # Check if hardware report is loaded
        if not self.controller.hardware_report:
            InfoBar.warning(
                title='Hardware Report Required',
                content='Please load a hardware report before building.',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
            return

        # Update UI state for build in progress
        self.build_in_progress = True
        self.build_successful = False
        self.build_btn.setEnabled(False)
        self.build_btn.setText("Building...")
        
        # Show and reset progress
        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Update status with icon
        self.update_status_icon("building")
        self.progress_label.setText("Preparing to build...")
        self.progress_label.setStyleSheet(f"color: {COLORS['primary']};")
        
        # Show statistics and activity cards
        self.stats_card.setVisible(True)
        self.activity_card.setVisible(True)
        self.classic_log_card.setVisible(True)
        
        # Reset statistics
        self.build_start_time = datetime.now()
        self.files_count_label.setText("0")
        self.current_phase_label.setText("Preparing")
        self.elapsed_time_label.setText("0s")
        
        # Start stats timer
        if self.stats_timer:
            self.stats_timer.stop()
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)  # Update every second
        
        # Clear previous log entries
        for entry in self.log_entries:
            entry.deleteLater()
        self.log_entries.clear()
        
        # Hide success card and clear log
        self.success_card.setVisible(False)
        self.instructions_after_build_card.setVisible(False)
        self.build_log.clear()
        
        # Add initial log entry to activity feed
        self.add_log_entry("Build process initiated", "step", FluentIcon.PLAY)
        self.add_log_entry(f"Target macOS: {self.controller.macos_version_text}", "info")
        self.add_log_entry(f"SMBIOS Model: {self.controller.smbios_model_text}", "info")
        if self.controller.needs_oclp:
            self.add_log_entry("OpenCore Legacy Patcher support enabled", "warning", FluentIcon.IMPORTANT)
        
        # Log start with enhanced header
        self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
        self.controller.log_message("🚀 OpenCore EFI Build Started", to_console=False, to_build_log=True)
        self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
        self.controller.log_message("", to_console=False, to_build_log=True)
        
        # Log build configuration
        self.controller.log_message("Build Configuration:", to_console=False, to_build_log=True)
        self.controller.log_message(f"  • macOS Version: {self.controller.macos_version_text}", to_console=False, to_build_log=True)
        self.controller.log_message(f"  • SMBIOS Model: {self.controller.smbios_model_text}", to_console=False, to_build_log=True)
        if self.controller.needs_oclp:
            self.controller.log_message(f"  • OpenCore Legacy Patcher: Required", to_console=False, to_build_log=True)
        self.controller.log_message("", to_console=False, to_build_log=True)

        # Call controller build method
        self.controller.build_efi()

    def update_status_icon(self, status):
        """Update status icon based on build state with improved visibility"""
        icon_size = 28  # Increased size for better visibility
        icon_map = {
            "building": (FluentIcon.SYNC, COLORS['primary']),
            "success": (FluentIcon.COMPLETED, COLORS['success']),
            "error": (FluentIcon.CLOSE, COLORS['error']),
        }
        
        if status in icon_map:
            icon, color = icon_map[status]
            pixmap = icon.icon(color=color).pixmap(icon_size, icon_size)
            self.status_icon_label.setPixmap(pixmap)

    def show_post_build_instructions(self, bios_requirements):
        """Display post-build instructions card with BIOS and USB mapping info"""
        # Clear existing content
        while self.instructions_after_content_layout.count():
            item = self.instructions_after_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # BIOS/UEFI Settings section
        if bios_requirements:
            bios_header = StrongBodyLabel("1. BIOS/UEFI Settings Required:")
            bios_header.setStyleSheet(f"color: {COLORS['warning_text']}; font-size: 14px;")
            self.instructions_after_content_layout.addWidget(bios_header)
            
            bios_text = "\n".join([f"  • {req}" for req in bios_requirements])
            bios_label = BodyLabel(bios_text)
            bios_label.setWordWrap(True)
            bios_label.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 10px;")
            self.instructions_after_content_layout.addWidget(bios_label)
            
            self.instructions_after_content_layout.addSpacing(SPACING['medium'])
        
        # USB Mapping section
        usb_header = StrongBodyLabel(f"{'2' if bios_requirements else '1'}. USB Port Mapping:")
        usb_header.setStyleSheet(f"color: {COLORS['warning_text']}; font-size: 14px;")
        self.instructions_after_content_layout.addWidget(usb_header)
        
        # Determine path separator based on OS
        path_sep = "\\" if platform.system() == "Windows" else "/"
        kexts_path = f"EFI{path_sep}OC{path_sep}Kexts"
        
        usb_instructions = [
            "Use USBToolBox tool to map USB ports",
            f"Add created UTBMap.kext into the {kexts_path} folder",
            f"Remove UTBDefault.kext from the {kexts_path} folder",
            "Edit config.plist using ProperTree:",
            "  - Open config.plist with ProperTree",
            "  - Run OC Snapshot (Command/Ctrl + R)",
            "  - Enable XhciPortLimit patch if you have more than 15 ports",
            "  - Save the file"
        ]
        
        usb_text = "\n".join([f"  • {inst}" for inst in usb_instructions])
        usb_label = BodyLabel(usb_text)
        usb_label.setWordWrap(True)
        usb_label.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 10px;")
        self.instructions_after_content_layout.addWidget(usb_label)
        
        # Show the card
        self.instructions_after_build_card.setVisible(True)

    def on_build_complete(self, success=True, bios_requirements=None):
        """Handle build completion with enhanced feedback"""
        self.build_in_progress = False
        self.build_successful = success
        
        # Stop stats timer
        if self.stats_timer:
            self.stats_timer.stop()
            self.update_stats()  # One final update
        
        if success:
            # Success state
            self.update_status_icon("success")
            self.progress_label.setText("✓ Build completed successfully!")
            self.progress_label.setStyleSheet(f"color: {COLORS['success']};")
            self.progress_bar.setValue(100)
            
            # Update phase
            self.current_phase_label.setText("Complete")
            
            # Add success log entries
            self.add_log_entry("Build completed successfully!", "success", FluentIcon.COMPLETED)
            self.add_log_entry("EFI folder is ready for installation", "success")
            
            # Show success card
            self.success_card.setVisible(True)
            
            # Show post-build instructions if we have requirements
            if bios_requirements is not None:
                self.show_post_build_instructions(bios_requirements)
                self.add_log_entry("Please review post-build instructions", "warning", FluentIcon.IMPORTANT)
            
            # Reset build button
            self.build_btn.setText("Build OpenCore EFI")
            self.build_btn.setEnabled(True)
            
            # Log completion
            self.controller.log_message("", to_console=False, to_build_log=True)
            self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
            self.controller.log_message("✓ Build Completed Successfully!", to_console=False, to_build_log=True)
            self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
            
            # Show success notification
            success_message = 'Your OpenCore EFI has been built successfully!'
            if bios_requirements is not None:
                success_message += ' Review the important instructions below.'
            
            InfoBar.success(
                title='Build Complete',
                content=success_message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
        else:
            # Error state
            self.update_status_icon("error")
            self.progress_label.setText("✗ Build failed - see log for details")
            self.progress_label.setStyleSheet(f"color: {COLORS['error']};")
            
            # Update phase
            self.current_phase_label.setText("Failed")
            
            # Add error log entry
            self.add_log_entry("Build failed - check details in log", "error", FluentIcon.CLOSE)
            
            # Reset build button
            self.build_btn.setText("Retry Build")
            self.build_btn.setEnabled(True)
            
            # Hide success card
            self.success_card.setVisible(False)
            
            # Log error
            self.controller.log_message("", to_console=False, to_build_log=True)
            self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
            self.controller.log_message("✗ Build Failed", to_console=False, to_build_log=True)
            self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
            
            # Show error notification
            InfoBar.error(
                title='Build Failed',
                content='An error occurred during the build. Check the log for details.',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )

    def open_result(self):
        """Open result folder"""
        import os
        import subprocess
        import platform

        result_dir = self.controller.ocpe.result_dir
        if os.path.exists(result_dir):
            if platform.system() == "Windows":
                os.startfile(result_dir)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", result_dir])
            else:
                subprocess.Popen(["xdg-open", result_dir])
        else:
            InfoBar.warning(
                title='Folder Not Found',
                content='The result folder does not exist yet.',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )

    def refresh(self):
        """Refresh page content"""
        # Reset UI state if not building
        if not self.build_in_progress:
            if self.build_successful:
                self.success_card.setVisible(True)
                self.progress_container.setVisible(True)
            else:
                self.success_card.setVisible(False)
                # Check if log has meaningful content
                log_text = self.build_log.toPlainText()
                if not log_text or log_text == DEFAULT_LOG_TEXT:
                    self.progress_container.setVisible(False)
