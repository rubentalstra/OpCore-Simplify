"""
Step 4: Build EFI - allows users to build their customized OpenCore EFI.
Enhanced with stunning UI/UX using qfluentwidgets components.
All build steps are visualized with proper widgets instead of plain text.
"""

import platform
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, CardWidget, TextEdit,
    StrongBodyLabel, ProgressBar, PrimaryPushButton, FluentIcon,
    ScrollArea, InfoBar, InfoBarPosition, TitleLabel, ProgressRing,
    TransparentToolButton, IconWidget, CaptionLabel, IndeterminateProgressRing,
    TableWidget, TableView, PushButton
)

from ..styles import COLORS, SPACING, RADIUS
from ..ui_utils import build_icon_label, create_step_indicator

# Constants for build log formatting
LOG_SEPARATOR = "═" * 60
DEFAULT_LOG_TEXT = "Build log will appear here..."
MAX_ACTIVITY_LOG_ENTRIES = 50  # Maximum number of entries to keep in activity feed for performance
MAX_PASSWORD_DISPLAY_LENGTH = 12  # Maximum length of password to display before truncating


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
        
        # Visual build component tracking
        self.download_cards = {}  # Component name -> card widget
        self.kext_install_widgets = {}  # Kext name -> widget
        self.acpi_patch_widgets = {}  # Patch name -> widget
        self.wifi_table = None  # WiFi profiles table
        self.codec_config_card = None  # Audio codec configuration card
        self.cleanup_list = None  # Cleanup files list
        
        # Build phase cards
        self.gathering_phase_card = None
        self.acpi_phase_card = None
        self.kext_phase_card = None
        self.config_phase_card = None
        self.cleanup_phase_card = None
        
        # Collection of all phase cards for easy iteration
        self.all_phase_cards = []
        
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

        # Live Build Activity Card (initially hidden) - ENHANCED LOG DISPLAY
        self.activity_card = CardWidget(self.scrollWidget)
        self.activity_card.setBorderRadius(RADIUS['card'])
        activity_card_layout = QVBoxLayout(self.activity_card)
        activity_card_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                                SPACING['large'], SPACING['large'])
        activity_card_layout.setSpacing(SPACING['medium'])
        
        # Activity header - simplified
        activity_header_layout = QHBoxLayout()
        activity_header_layout.setSpacing(SPACING['medium'])
        activity_icon = build_icon_label(FluentIcon.SYNC, COLORS['primary'], size=24)
        activity_header_layout.addWidget(activity_icon)
        
        activity_title = SubtitleLabel("Build Activity")
        activity_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600;")
        activity_header_layout.addWidget(activity_title)
        activity_header_layout.addStretch()
        activity_card_layout.addLayout(activity_header_layout)
        
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
        activity_scroll.setMinimumHeight(250)
        activity_scroll.setMaximumHeight(400)
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

        # Build Phase Visualization Cards (initially hidden)
        # These cards show visual representations of each build phase
        
        # 1. File Gathering Phase Card
        self.gathering_phase_card = self.create_build_phase_card(
            "File Gathering Phase",
            FluentIcon.DOWNLOAD,
            "Downloading and extracting OpenCore components and kexts"
        )
        layout.addWidget(self.gathering_phase_card)
        
        # 2. ACPI Phase Card
        self.acpi_phase_card = self.create_build_phase_card(
            "ACPI Patches Phase",
            FluentIcon.TAG,  # Changed from LABEL
            "Applying ACPI patches and DSDT modifications"
        )
        layout.addWidget(self.acpi_phase_card)
        
        # 3. Kext Installation Phase Card
        self.kext_phase_card = self.create_build_phase_card(
            "Kext Installation Phase",
            FluentIcon.DEVELOPER_TOOLS,  # Changed from PLUG
            "Installing and configuring kernel extensions"
        )
        layout.addWidget(self.kext_phase_card)
        
        # 4. Configuration Phase Card  
        self.config_phase_card = self.create_build_phase_card(
            "Configuration Phase",
            FluentIcon.SETTING,
            "Generating config.plist with customized settings"
        )
        layout.addWidget(self.config_phase_card)
        
        # 5. Cleanup Phase Card
        self.cleanup_phase_card = self.create_build_phase_card(
            "Cleanup Phase",
            FluentIcon.DELETE,
            "Removing unused drivers, resources, and tools"
        )
        layout.addWidget(self.cleanup_phase_card)
        
        # Store all phase cards for easy iteration
        self.all_phase_cards = [
            self.gathering_phase_card,
            self.acpi_phase_card,
            self.kext_phase_card,
            self.config_phase_card,
            self.cleanup_phase_card
        ]

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
        self.toggle_log_btn = TransparentToolButton(FluentIcon.DOWN)  # Changed from CHEVRON_DOWN
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
            self.toggle_log_btn.setIcon(FluentIcon.DOWN)  # Changed from CHEVRON_DOWN
        else:
            self.toggle_log_btn.setIcon(FluentIcon.UP)  # Changed from CHEVRON_UP
    
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
            "warning": (FluentIcon.MEGAPHONE, COLORS['warning']),  # Changed from IMPORTANT
            "error": (FluentIcon.CLOSE, COLORS['error']),
            "step": (FluentIcon.CARE_RIGHT_SOLID, COLORS['primary']),  # Changed from CHEVRON_RIGHT
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
    
    def create_build_phase_card(self, title, icon, description):
        """Create a collapsible card for a build phase with visual content area"""
        card = CardWidget(self.scrollWidget)
        card.setBorderRadius(RADIUS['card'])
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                       SPACING['large'], SPACING['large'])
        card_layout.setSpacing(SPACING['medium'])
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING['medium'])
        
        phase_icon = build_icon_label(icon, COLORS['primary'], size=28)
        header_layout.addWidget(phase_icon)
        
        phase_title = SubtitleLabel(title)
        phase_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600;")
        header_layout.addWidget(phase_title)
        
        header_layout.addStretch()
        
        # Status indicator
        status_label = CaptionLabel("Pending")
        status_label.setObjectName("statusLabel")
        status_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        header_layout.addWidget(status_label)
        
        card_layout.addLayout(header_layout)
        
        # Description
        desc_label = BodyLabel(description)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        card_layout.addWidget(desc_label)
        
        # Content area (will be populated dynamically)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, SPACING['small'], 0, 0)
        content_layout.setSpacing(SPACING['small'])
        content_widget.setObjectName("contentWidget")
        card_layout.addWidget(content_widget)
        
        card.setVisible(False)
        return card
    
    def update_phase_status(self, phase_card, status, color=None):
        """Update the status of a build phase card"""
        if not phase_card:
            return
        
        status_label = phase_card.findChild(CaptionLabel, "statusLabel")
        if status_label:
            status_label.setText(status)
            if color:
                status_label.setStyleSheet(f"color: {color};")
    
    def add_download_component_card(self, component_name, version=""):
        """Add a visual card for a downloading component"""
        if not self.gathering_phase_card:
            return
        
        content_widget = self.gathering_phase_card.findChild(QWidget, "contentWidget")
        if not content_widget:
            return
        
        # Create component download widget
        comp_widget = QWidget()
        comp_layout = QHBoxLayout(comp_widget)
        comp_layout.setContentsMargins(SPACING['medium'], SPACING['small'],
                                       SPACING['medium'], SPACING['small'])
        comp_layout.setSpacing(SPACING['medium'])
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(FluentIcon.DOWNLOAD.icon(color=COLORS['primary']).pixmap(20, 20))
        icon_label.setFixedSize(24, 24)
        comp_layout.addWidget(icon_label)
        
        # Name and version
        name_label = BodyLabel(f"{component_name} {version}".strip())
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        comp_layout.addWidget(name_label, stretch=1)
        
        # Status
        status_label = CaptionLabel("Downloading...")
        status_label.setObjectName("compStatus")
        status_label.setStyleSheet(f"color: {COLORS['primary']};")
        comp_layout.addWidget(status_label)
        
        comp_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 120, 212, 0.05);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        
        content_widget.layout().addWidget(comp_widget)
        self.download_cards[component_name] = comp_widget
    
    def update_download_component_status(self, component_name, status, is_success=True):
        """Update the status of a downloading component"""
        if component_name not in self.download_cards:
            return
        
        comp_widget = self.download_cards[component_name]
        status_label = comp_widget.findChild(CaptionLabel, "compStatus")
        
        if status_label:
            status_label.setText(status)
            color = COLORS['success'] if is_success else COLORS['error']
            status_label.setStyleSheet(f"color: {color};")
        
        # Update icon
        icon_labels = comp_widget.findChildren(QLabel)
        if icon_labels:
            new_icon = FluentIcon.COMPLETED if is_success else FluentIcon.CLOSE
            icon_labels[0].setPixmap(new_icon.icon(color=color).pixmap(20, 20))
    
    def create_wifi_profiles_table(self, profiles):
        """Create a TableWidget to display WiFi profiles"""
        if not self.kext_phase_card or not profiles:
            return
        
        content_widget = self.kext_phase_card.findChild(QWidget, "contentWidget")
        if not content_widget:
            return
        
        # Header
        wifi_header = StrongBodyLabel("📶 WiFi Profiles Configured")
        wifi_header.setStyleSheet(f"color: {COLORS['text_primary']}; margin-top: {SPACING['medium']}px;")
        content_widget.layout().addWidget(wifi_header)
        
        # Create table
        self.wifi_table = TableWidget()
        self.wifi_table.setColumnCount(3)
        self.wifi_table.setHorizontalHeaderLabels(["SSID", "Password", "Status"])
        self.wifi_table.setRowCount(len(profiles))
        
        # Style the table
        self.wifi_table.setStyleSheet(f"""
            TableWidget {{
                background-color: rgba(0, 0, 0, 0.02);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        
        # Populate table
        for row, (ssid, password) in enumerate(profiles):
            # SSID
            ssid_item = QTableWidgetItem(ssid)
            ssid_item.setFlags(ssid_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.wifi_table.setItem(row, 0, ssid_item)
            
            # Password (masked)
            masked_password = "•" * min(len(password), MAX_PASSWORD_DISPLAY_LENGTH) if password else "(Open Network)"
            password_item = QTableWidgetItem(masked_password)
            password_item.setFlags(password_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.wifi_table.setItem(row, 1, password_item)
            
            # Status
            status_item = QTableWidgetItem("✓ Configured")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.wifi_table.setItem(row, 2, status_item)
        
        # Resize columns
        header = self.wifi_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.wifi_table.setMaximumHeight(200)
        content_widget.layout().addWidget(self.wifi_table)
    
    def add_acpi_patch_item(self, patch_name, status="Applied"):
        """Add a visual item for an ACPI patch"""
        if not self.acpi_phase_card:
            return
        
        content_widget = self.acpi_phase_card.findChild(QWidget, "contentWidget")
        if not content_widget:
            return
        
        # Create patch item
        patch_widget = QWidget()
        patch_layout = QHBoxLayout(patch_widget)
        patch_layout.setContentsMargins(SPACING['medium'], SPACING['small'],
                                        SPACING['medium'], SPACING['small'])
        patch_layout.setSpacing(SPACING['medium'])
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(FluentIcon.COMPLETED.icon(color=COLORS['success']).pixmap(16, 16))
        icon_label.setFixedSize(20, 20)
        patch_layout.addWidget(icon_label)
        
        # Patch name
        name_label = BodyLabel(patch_name)
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        patch_layout.addWidget(name_label, stretch=1)
        
        # Status
        status_label = CaptionLabel(status)
        status_label.setStyleSheet(f"color: {COLORS['success']};")
        patch_layout.addWidget(status_label)
        
        patch_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(16, 124, 16, 0.05);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        
        content_widget.layout().addWidget(patch_widget)
        self.acpi_patch_widgets[patch_name] = patch_widget
    
    def add_kext_item(self, kext_name, status="Installed"):
        """Add a visual item for an installed kext"""
        if not self.kext_phase_card:
            return
        
        content_widget = self.kext_phase_card.findChild(QWidget, "contentWidget")
        if not content_widget:
            return
        
        # Create kext item
        kext_widget = QWidget()
        kext_layout = QHBoxLayout(kext_widget)
        kext_layout.setContentsMargins(SPACING['medium'], SPACING['small'],
                                       SPACING['medium'], SPACING['small'])
        kext_layout.setSpacing(SPACING['medium'])
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(FluentIcon.DEVELOPER_TOOLS.icon(color=COLORS['success']).pixmap(16, 16))  # Changed from PLUG
        icon_label.setFixedSize(20, 20)
        kext_layout.addWidget(icon_label)
        
        # Kext name
        name_label = BodyLabel(kext_name)
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        kext_layout.addWidget(name_label, stretch=1)
        
        # Status
        status_label = CaptionLabel(status)
        status_label.setStyleSheet(f"color: {COLORS['success']};")
        kext_layout.addWidget(status_label)
        
        kext_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(16, 124, 16, 0.05);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        
        content_widget.layout().addWidget(kext_widget)
        self.kext_install_widgets[kext_name] = kext_widget
    
    def add_codec_configuration(self, codec_name, layout_id):
        """Add audio codec configuration visualization"""
        if not self.config_phase_card:
            return
        
        content_widget = self.config_phase_card.findChild(QWidget, "contentWidget")
        if not content_widget:
            return
        
        # Codec card
        codec_widget = QWidget()
        codec_layout = QVBoxLayout(codec_widget)
        codec_layout.setContentsMargins(SPACING['medium'], SPACING['medium'],
                                        SPACING['medium'], SPACING['medium'])
        codec_layout.setSpacing(SPACING['small'])
        
        # Header
        header_label = StrongBodyLabel("🔊 Audio Configuration")
        header_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        codec_layout.addWidget(header_label)
        
        # Details
        codec_label = BodyLabel(f"Codec: {codec_name}")
        codec_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        codec_layout.addWidget(codec_label)
        
        layout_label = BodyLabel(f"Layout ID: {layout_id}")
        layout_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        codec_layout.addWidget(layout_label)
        
        codec_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 120, 212, 0.05);
                border-radius: {RADIUS['small']}px;
            }}
        """)
        
        content_widget.layout().addWidget(codec_widget)
        self.codec_config_card = codec_widget

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
        
        # Show activity card
        self.activity_card.setVisible(True)
        self.classic_log_card.setVisible(True)
        
        # Track build start time
        self.build_start_time = datetime.now()
        
        # Clear previous log entries
        for entry in self.log_entries:
            entry.deleteLater()
        self.log_entries.clear()
        
        # Reset and hide all phase cards
        self.download_cards.clear()
        self.kext_install_widgets.clear()
        self.acpi_patch_widgets.clear()
        
        for phase_card in self.all_phase_cards:
            if phase_card:
                phase_card.setVisible(False)
                self.update_phase_status(phase_card, "Pending", COLORS['text_tertiary'])
                # Clear content
                content_widget = phase_card.findChild(QWidget, "contentWidget")
                if content_widget and content_widget.layout():
                    while content_widget.layout().count():
                        item = content_widget.layout().takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
        
        # Hide success card and clear log
        self.success_card.setVisible(False)
        self.instructions_after_build_card.setVisible(False)
        self.build_log.clear()
        
        # Add initial log entry to activity feed
        self.add_log_entry("Build process initiated", "step", FluentIcon.DEVELOPER_TOOLS)  # Changed from PLAY
        self.add_log_entry(f"Target macOS: {self.controller.macos_version_text}", "info")
        self.add_log_entry(f"SMBIOS Model: {self.controller.smbios_model_text}", "info")
        if self.controller.needs_oclp:
            self.add_log_entry("OpenCore Legacy Patcher support enabled", "warning", FluentIcon.MEGAPHONE)  # Changed from IMPORTANT
        
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
        
        if success:
            # Success state
            self.update_status_icon("success")
            self.progress_label.setText("✓ Build completed successfully!")
            self.progress_label.setStyleSheet(f"color: {COLORS['success']};")
            self.progress_bar.setValue(100)
            
            # Add success log entries
            self.add_log_entry("Build completed successfully!", "success", FluentIcon.COMPLETED)
            self.add_log_entry("EFI folder is ready for installation", "success")
            
            # Show success card
            self.success_card.setVisible(True)
            
            # Show post-build instructions if we have requirements
            if bios_requirements is not None:
                self.show_post_build_instructions(bios_requirements)
                self.add_log_entry("Please review post-build instructions", "warning", FluentIcon.MEGAPHONE)  # Changed from IMPORTANT
            
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
