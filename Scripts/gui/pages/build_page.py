"""
Step 4: Build EFI - qfluentwidgets version with enhanced UI/UX
"""

import platform
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    PushButton, SubtitleLabel, BodyLabel, CardWidget, TextEdit,
    StrongBodyLabel, ProgressBar, PrimaryPushButton, FluentIcon,
    ScrollArea, InfoBar, InfoBarPosition, GroupHeaderCardWidget,
    TitleLabel
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
        """Setup the build page UI with improved qfluentwidgets components"""
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
        step_label = BodyLabel("STEP 4 OF 4")
        step_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")
        layout.addWidget(step_label)

        # Title section with better typography
        title_label = TitleLabel("Build OpenCore EFI")
        layout.addWidget(title_label)

        subtitle_label = BodyLabel("Build your customized OpenCore EFI ready for installation")
        subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle_label)

        layout.addSpacing(SPACING['medium'])

        # Build instructions card using GroupHeaderCardWidget
        instructions_card = GroupHeaderCardWidget(self.scrollWidget)
        instructions_card.setTitle("Before You Build")
        instructions_card.setBorderRadius(RADIUS['card'])
        
        # Add icon to header
        instructions_icon_label = build_icon_label(FluentIcon.INFO, COLORS['note_text'], size=24)
        instructions_card.headerLayout.insertWidget(0, instructions_icon_label)
        
        # Instructions content using addGroup
        instructions_content = QWidget()
        instructions_layout = QVBoxLayout(instructions_content)
        instructions_layout.setContentsMargins(SPACING['medium'], SPACING['small'], SPACING['medium'], SPACING['medium'])
        
        instructions_text = BodyLabel(
            "The build process will:\n\n"
            "• Download the latest OpenCore bootloader and required kexts\n"
            "• Apply your customized ACPI patches and configurations\n"
            "• Generate a complete EFI folder ready for installation\n\n"
            "⏱️ This process typically takes 2-5 minutes depending on your internet connection.\n"
            "📊 Progress will be shown below with real-time status updates."
        )
        instructions_text.setWordWrap(True)
        instructions_text.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.8;")
        instructions_layout.addWidget(instructions_text)
        
        instructions_card.addGroup(FluentIcon.INFO, "Build Process", "What happens during the build", instructions_content)
        
        # Style the instructions card
        instructions_card.card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['note_bg']};
                border: 1px solid rgba(21, 101, 192, 0.15);
            }}
        """)
        
        layout.addWidget(instructions_card)

        # Build control card using GroupHeaderCardWidget  
        build_control_card = GroupHeaderCardWidget(self.scrollWidget)
        build_control_card.setTitle("Build Control")
        build_control_card.setBorderRadius(RADIUS['card'])
        
        # Add icon to build control header
        build_icon_header = build_icon_label(FluentIcon.DEVELOPER_TOOLS, COLORS['primary'], size=24)
        build_control_card.headerLayout.insertWidget(0, build_icon_header)

        # Build button with better styling
        build_btn_container = QWidget()
        build_btn_layout = QVBoxLayout(build_btn_container)
        build_btn_layout.setContentsMargins(SPACING['medium'], SPACING['small'], SPACING['medium'], SPACING['small'])
        build_btn_layout.setSpacing(SPACING['small'])
        
        self.build_btn = PrimaryPushButton(FluentIcon.DEVELOPER_TOOLS, "Build OpenCore EFI")
        self.build_btn.clicked.connect(self.start_build)
        self.build_btn.setFixedHeight(44)
        self.controller.build_btn = self.build_btn
        build_btn_layout.addWidget(self.build_btn)
        
        build_hint = BodyLabel("Click to start building your customized EFI")
        build_hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        build_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        build_btn_layout.addWidget(build_hint)
        
        build_control_card.addGroup(FluentIcon.PLAY, "Start Build", "Click the button below to begin", build_btn_container)

        # Progress section (initially hidden)
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(SPACING['medium'], SPACING['medium'], SPACING['medium'], SPACING['medium'])
        progress_layout.setSpacing(SPACING['medium'])

        # Progress status with larger, more visible icon
        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING['medium'])
        
        self.status_icon_label = QLabel()
        self.status_icon_label.setFixedSize(24, 24)
        status_row.addWidget(self.status_icon_label)
        
        self.progress_label = StrongBodyLabel("Ready to build")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        status_row.addWidget(self.progress_label)
        status_row.addStretch()
        
        progress_layout.addLayout(status_row)

        # Progress bar with better visibility
        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.controller.progress_bar = self.progress_bar
        progress_layout.addWidget(self.progress_bar)
        
        self.controller.progress_label = self.progress_label
        self.progress_container.setVisible(False)
        
        build_control_card.addGroup(FluentIcon.SYNC, "Build Progress", "Current build status", self.progress_container)
        layout.addWidget(build_control_card)

        # Build log card using GroupHeaderCardWidget
        log_card = GroupHeaderCardWidget(self.scrollWidget)
        log_card.setTitle("Build Log")
        log_card.setBorderRadius(RADIUS['card'])
        
        # Add icon to log header
        log_icon_header = build_icon_label(FluentIcon.DOCUMENT, COLORS['primary'], size=24)
        log_card.headerLayout.insertWidget(0, log_icon_header)
        
        # Log description and content
        log_content_widget = QWidget()
        log_content_layout = QVBoxLayout(log_content_widget)
        log_content_layout.setContentsMargins(0, 0, 0, 0)
        log_content_layout.setSpacing(SPACING['small'])
        
        log_description = BodyLabel("Detailed build process information and status updates")
        log_description.setStyleSheet(f"color: {COLORS['text_secondary']};")
        log_content_layout.addWidget(log_description)

        # Build log text area with improved styling
        log_container = QWidget()
        log_container_layout = QVBoxLayout(log_container)
        log_container_layout.setContentsMargins(0, SPACING['small'], 0, 0)
        
        self.build_log = TextEdit()
        self.build_log.setReadOnly(True)
        self.build_log.setPlainText(DEFAULT_LOG_TEXT)
        self.build_log.setMinimumHeight(350)
        self.build_log.setStyleSheet(f"""
            TextEdit {{
                background-color: rgba(0, 0, 0, 0.02);
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: {RADIUS['small']}px;
                padding: {SPACING['medium']}px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
            }}
        """)
        self.controller.build_log = self.build_log
        log_container_layout.addWidget(self.build_log)
        
        log_content_layout.addWidget(log_container)
        
        log_card.addGroup(FluentIcon.DOCUMENT, "Log Output", "Real-time build process logs", log_content_widget)
        layout.addWidget(log_card)

        # Success card using GroupHeaderCardWidget (initially hidden)
        self.success_card = GroupHeaderCardWidget(self.scrollWidget)
        self.success_card.setTitle("Build Completed Successfully!")
        self.success_card.setBorderRadius(RADIUS['card'])
        
        # Add success icon to header
        success_icon_header = build_icon_label(FluentIcon.COMPLETED, COLORS['success'], size=32)
        self.success_card.headerLayout.insertWidget(0, success_icon_header)
        
        # Success content
        success_content = QWidget()
        success_content_layout = QVBoxLayout(success_content)
        success_content_layout.setContentsMargins(SPACING['medium'], SPACING['small'], SPACING['medium'], SPACING['medium'])
        success_content_layout.setSpacing(SPACING['medium'])
        
        success_message = BodyLabel(
            "🎉 Your OpenCore EFI has been built successfully!\n\n"
            "The EFI folder is ready for installation. You can now:\n"
            "• Open the result folder to view your EFI\n"
            "• Review the post-build instructions below\n"
            "• Copy the EFI to your USB drive or EFI partition"
        )
        success_message.setWordWrap(True)
        success_message.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.8;")
        success_content_layout.addWidget(success_message)

        # Action buttons with better layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(SPACING['medium'])
        
        self.open_result_btn = PrimaryPushButton(FluentIcon.FOLDER, "Open Result Folder")
        self.open_result_btn.clicked.connect(self.open_result)
        self.open_result_btn.setFixedHeight(40)
        buttons_layout.addWidget(self.open_result_btn)
        
        buttons_layout.addStretch()
        success_content_layout.addLayout(buttons_layout)
        
        self.success_card.addGroup(FluentIcon.COMPLETED, "Success", "Your EFI is ready!", success_content)
        self.controller.open_result_btn = self.open_result_btn
        
        # Style the success card
        self.success_card.card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['success_bg']};
                border: 1px solid rgba(16, 124, 16, 0.2);
            }}
        """)
        
        self.success_card.setVisible(False)
        layout.addWidget(self.success_card)

        # Post-build instructions card using GroupHeaderCardWidget (initially hidden)
        self.instructions_after_build_card = GroupHeaderCardWidget(self.scrollWidget)
        self.instructions_after_build_card.setTitle("Important: Before Using Your EFI")
        self.instructions_after_build_card.setBorderRadius(RADIUS['card'])
        
        # Add warning icon to header
        warning_icon_header = build_icon_label(FluentIcon.MEGAPHONE, COLORS['warning_text'], size=28)
        self.instructions_after_build_card.headerLayout.insertWidget(0, warning_icon_header)
        
        # Instructions content container
        instructions_after_container = QWidget()
        instructions_after_container_layout = QVBoxLayout(instructions_after_container)
        instructions_after_container_layout.setContentsMargins(SPACING['medium'], SPACING['small'], SPACING['medium'], SPACING['medium'])
        instructions_after_container_layout.setSpacing(SPACING['small'])
        
        instructions_after_intro = BodyLabel(
            "Please complete these important steps before using the built EFI:"
        )
        instructions_after_intro.setStyleSheet(f"color: {COLORS['text_secondary']};")
        instructions_after_container_layout.addWidget(instructions_after_intro)
        
        # Content area for requirements (will be populated dynamically)
        self.instructions_after_content = QWidget()
        self.instructions_after_content_layout = QVBoxLayout(self.instructions_after_content)
        self.instructions_after_content_layout.setContentsMargins(0, SPACING['medium'], 0, 0)
        self.instructions_after_content_layout.setSpacing(SPACING['medium'])
        instructions_after_container_layout.addWidget(self.instructions_after_content)
        
        self.instructions_after_build_card.addGroup(FluentIcon.IMPORTANT, "Post-Build Steps", "Follow these steps before using your EFI", instructions_after_container)
        
        # Style the warning card
        self.instructions_after_build_card.card.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['warning_bg']};
                border: 1px solid rgba(245, 124, 0, 0.25);
            }}
        """)
        
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
        self.progress_label.setText("Preparing to build...")
        self.progress_label.setStyleSheet(f"color: {COLORS['primary']};")
        
        # Hide success card and clear log
        self.success_card.setVisible(False)
        self.instructions_after_build_card.setVisible(False)
        self.build_log.clear()
        
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
        icon_size = 24  # Increased size for better visibility
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
