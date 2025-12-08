"""
Step 4: Build EFI - qfluentwidgets version with enhanced UI/UX
"""

import platform
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    PushButton, SubtitleLabel, BodyLabel, CardWidget, TextEdit,
    StrongBodyLabel, ProgressBar, PrimaryPushButton, FluentIcon,
    ScrollArea, InfoBar, InfoBarPosition
)

from ..styles import COLORS, SPACING, RADIUS

# Constants for build log formatting
LOG_SEPARATOR = "═" * 60
DEFAULT_LOG_TEXT = "Build log will appear here..."


def build_icon_label(icon, color, size=32):
    """Create a QLabel with a tinted Fluent icon pixmap"""
    label = QLabel()
    label.setPixmap(icon.icon(color=color).pixmap(size, size))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedSize(size + 12, size + 12)
    return label


class BuildPage(ScrollArea):
    """Step 4: Build OpenCore EFI with enhanced UI/UX"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("buildPage")
        self.controller = parent
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.build_in_progress = False
        self.build_successful = False
        self.setup_ui()

    def setup_ui(self):
        """Setup the build page UI with ScrollArea for better content handling"""
        # Configure scroll area
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.enableTransparentBackground()

        # Set layout spacing and margins
        self.expandLayout.setContentsMargins(SPACING['xxlarge'], SPACING['xlarge'],
                                             SPACING['xxlarge'], SPACING['xlarge'])
        self.expandLayout.setSpacing(SPACING['large'])

        layout = self.expandLayout

        # Step indicator
        step_label = BodyLabel("STEP 4 OF 4")
        step_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")
        layout.addWidget(step_label)

        # Title section
        title_label = SubtitleLabel("Build OpenCore EFI")
        layout.addWidget(title_label)

        subtitle_label = BodyLabel("Build your customized OpenCore EFI")
        subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle_label)

        layout.addSpacing(SPACING['large'])

        # Instructions card (helpful info before build)
        instructions_card = CardWidget()
        instructions_card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['note_bg']};
                border: 1px solid rgba(21, 101, 192, 0.2);
                border-radius: {RADIUS['card']}px;
            }}
        """)
        instructions_layout = QHBoxLayout(instructions_card)
        instructions_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                               SPACING['large'], SPACING['large'])
        instructions_layout.setSpacing(SPACING['large'])

        info_icon = build_icon_label(FluentIcon.INFO, COLORS['note_text'], size=40)
        instructions_layout.addWidget(info_icon)

        instructions_text_layout = QVBoxLayout()
        instructions_text_layout.setSpacing(SPACING['small'])

        instructions_title = StrongBodyLabel("Before You Build")
        instructions_title.setStyleSheet(f"color: {COLORS['note_text']};")
        instructions_text_layout.addWidget(instructions_title)

        instructions_body = BodyLabel(
            "The build process will:\n"
            "• Download the latest OpenCore bootloader and required kexts\n"
            "• Apply your customized ACPI patches and configurations\n"
            "• Generate a complete EFI folder ready for installation\n\n"
            "This process may take a few minutes depending on your internet connection."
        )
        instructions_body.setWordWrap(True)
        instructions_body.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.6;")
        instructions_text_layout.addWidget(instructions_body)

        instructions_layout.addLayout(instructions_text_layout)
        layout.addWidget(instructions_card)

        # Build control card
        build_card = CardWidget()
        build_layout = QVBoxLayout(build_card)
        build_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                        SPACING['large'], SPACING['large'])
        build_layout.setSpacing(SPACING['medium'])

        card_title = StrongBodyLabel("Build Control")
        build_layout.addWidget(card_title)

        # Build button
        self.build_btn = PrimaryPushButton(
            FluentIcon.DEVELOPER_TOOLS, "Build OpenCore EFI")
        self.build_btn.clicked.connect(self.start_build)
        self.build_btn.setFixedHeight(40)
        self.controller.build_btn = self.build_btn
        build_layout.addWidget(self.build_btn)

        # Progress section (initially hidden)
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, SPACING['medium'], 0, 0)
        progress_layout.setSpacing(SPACING['small'])

        # Progress status with icon
        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING['small'])
        
        self.status_icon_label = QLabel()
        self.status_icon_label.setFixedSize(20, 20)
        status_row.addWidget(self.status_icon_label)
        
        self.progress_label = BodyLabel("Ready to build")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        status_row.addWidget(self.progress_label)
        status_row.addStretch()
        
        progress_layout.addLayout(status_row)

        # Progress bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        self.controller.progress_bar = self.progress_bar
        progress_layout.addWidget(self.progress_bar)
        
        self.controller.progress_label = self.progress_label
        self.progress_container.setVisible(False)
        build_layout.addWidget(self.progress_container)

        layout.addWidget(build_card)

        # Build log card
        log_card = CardWidget()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                      SPACING['large'], SPACING['large'])
        log_layout.setSpacing(SPACING['medium'])

        log_title = StrongBodyLabel("Build Log")
        log_layout.addWidget(log_title)

        log_subtitle = BodyLabel("Detailed build process information")
        log_subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        log_layout.addWidget(log_subtitle)

        # Build log text area
        self.build_log = TextEdit()
        self.build_log.setReadOnly(True)
        self.build_log.setPlainText(DEFAULT_LOG_TEXT)
        self.build_log.setMinimumHeight(300)
        self.controller.build_log = self.build_log
        log_layout.addWidget(self.build_log)

        layout.addWidget(log_card)

        # Success card (initially hidden)
        self.success_card = CardWidget()
        self.success_card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['success_bg']};
                border: 1px solid rgba(16, 124, 16, 0.2);
                border-radius: {RADIUS['card']}px;
            }}
        """)
        success_layout = QVBoxLayout(self.success_card)
        success_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                          SPACING['large'], SPACING['large'])
        success_layout.setSpacing(SPACING['medium'])

        # Success header with icon
        success_header = QHBoxLayout()
        success_header.setSpacing(SPACING['large'])
        
        success_icon = build_icon_label(FluentIcon.COMPLETED, COLORS['success'], size=48)
        success_header.addWidget(success_icon)
        
        success_text_layout = QVBoxLayout()
        success_text_layout.setSpacing(SPACING['tiny'])
        
        success_title = StrongBodyLabel("Build Completed Successfully!")
        success_title.setStyleSheet(f"color: {COLORS['success']}; font-size: 16px;")
        success_text_layout.addWidget(success_title)
        
        success_subtitle = BodyLabel("Your OpenCore EFI is ready to use")
        success_subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        success_text_layout.addWidget(success_subtitle)
        
        success_header.addLayout(success_text_layout)
        success_header.addStretch()
        success_layout.addLayout(success_header)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(SPACING['medium'])
        
        self.open_result_btn = PrimaryPushButton(FluentIcon.FOLDER, "Open Result Folder")
        self.open_result_btn.clicked.connect(self.open_result)
        self.open_result_btn.setFixedHeight(36)
        buttons_layout.addWidget(self.open_result_btn)
        
        buttons_layout.addStretch()
        success_layout.addLayout(buttons_layout)
        
        self.controller.open_result_btn = self.open_result_btn
        self.success_card.setVisible(False)
        layout.addWidget(self.success_card)

        # Post-build instructions card (initially hidden)
        self.instructions_after_build_card = CardWidget()
        self.instructions_after_build_card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['warning_bg']};
                border: 1px solid rgba(245, 124, 0, 0.25);
                border-radius: {RADIUS['card']}px;
            }}
        """)
        instructions_after_layout = QVBoxLayout(self.instructions_after_build_card)
        instructions_after_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                                     SPACING['large'], SPACING['large'])
        instructions_after_layout.setSpacing(SPACING['medium'])

        # Header with icon
        instructions_after_header = QHBoxLayout()
        instructions_after_header.setSpacing(SPACING['large'])
        
        warning_icon = build_icon_label(FluentIcon.MEGAPHONE, COLORS['warning_text'], size=40)
        instructions_after_header.addWidget(warning_icon)
        
        instructions_after_text_layout = QVBoxLayout()
        instructions_after_text_layout.setSpacing(SPACING['tiny'])
        
        instructions_after_title = StrongBodyLabel("Important: Before Using Your EFI")
        instructions_after_title.setStyleSheet(f"color: {COLORS['warning_text']}; font-size: 16px;")
        instructions_after_text_layout.addWidget(instructions_after_title)
        
        instructions_after_subtitle = BodyLabel("Please complete these steps before using the built EFI")
        instructions_after_subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        instructions_after_text_layout.addWidget(instructions_after_subtitle)
        
        instructions_after_header.addLayout(instructions_after_text_layout)
        instructions_after_header.addStretch()
        instructions_after_layout.addLayout(instructions_after_header)

        # Content area for requirements (will be populated dynamically)
        self.instructions_after_content = QWidget()
        self.instructions_after_content_layout = QVBoxLayout(self.instructions_after_content)
        self.instructions_after_content_layout.setContentsMargins(0, SPACING['small'], 0, 0)
        self.instructions_after_content_layout.setSpacing(SPACING['medium'])
        instructions_after_layout.addWidget(self.instructions_after_content)
        
        self.instructions_after_build_card.setVisible(False)
        layout.addWidget(self.instructions_after_build_card)

        layout.addStretch()

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
        self.progress_label.setText("Initializing build process...")
        self.progress_label.setStyleSheet(f"color: {COLORS['primary']};")
        
        # Hide success card and clear log
        self.success_card.setVisible(False)
        self.build_log.clear()
        
        # Log start with separator
        self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
        self.controller.log_message("Starting OpenCore EFI Build Process", to_console=False, to_build_log=True)
        self.controller.log_message(LOG_SEPARATOR, to_console=False, to_build_log=True)
        self.controller.log_message("", to_console=False, to_build_log=True)

        # Call controller build method
        self.controller.build_efi()

    def update_status_icon(self, status):
        """Update status icon based on build state"""
        icon_map = {
            "building": (FluentIcon.SYNC, COLORS['primary']),
            "success": (FluentIcon.COMPLETED, COLORS['success']),
            "error": (FluentIcon.CLOSE, COLORS['error']),
        }
        
        if status in icon_map:
            icon, color = icon_map[status]
            pixmap = icon.icon(color=color).pixmap(20, 20)
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
            
            # Show success card
            self.success_card.setVisible(True)
            
            # Show post-build instructions if we have requirements
            if bios_requirements is not None:
                self.show_post_build_instructions(bios_requirements)
            
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
