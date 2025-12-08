"""
Config.plist Editor Page - TreeView-based plist editor with OC Snapshot functionality
"""

import os
import plistlib
import hashlib
import shutil
from collections import OrderedDict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QDialog,
    QDialogButtonBox, QLabel, QCheckBox, QComboBox, QSpinBox,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    PushButton, SubtitleLabel, BodyLabel, CardWidget,
    StrongBodyLabel, PrimaryPushButton, FluentIcon,
    InfoBar, InfoBarPosition, MessageBox, ComboBox as FluentComboBox,
    ToolButton
)

from ..styles import COLORS, SPACING


class PlistTreeWidget(QTreeWidget):
    """Custom TreeWidget for displaying and editing plist data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Key", "Type", "Value"])
        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 400)
        self.setAlternatingRowColors(True)
        self.itemDoubleClicked.connect(self.edit_item)
        
    def populate_tree(self, data, parent=None):
        """Populate tree with plist data"""
        if parent is None:
            self.clear()
            parent = self.invisibleRootItem()
            
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent)
                item.setText(0, str(key))
                self._set_item_value(item, value)
                if isinstance(value, (dict, list)):
                    self.populate_tree(value, item)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem(parent)
                item.setText(0, f"Item {i}")
                self._set_item_value(item, value)
                if isinstance(value, (dict, list)):
                    self.populate_tree(value, item)
    
    def _set_item_value(self, item, value):
        """Set item type and value based on data type"""
        if isinstance(value, bool):
            item.setText(1, "Boolean")
            item.setText(2, "true" if value else "false")
            item.setData(2, Qt.ItemDataRole.UserRole, value)
        elif isinstance(value, int):
            item.setText(1, "Number")
            item.setText(2, str(value))
            item.setData(2, Qt.ItemDataRole.UserRole, value)
        elif isinstance(value, str):
            item.setText(1, "String")
            item.setText(2, value)
            item.setData(2, Qt.ItemDataRole.UserRole, value)
        elif isinstance(value, bytes):
            item.setText(1, "Data")
            item.setText(2, value.hex()[:50] + "..." if len(value) > 25 else value.hex())
            item.setData(2, Qt.ItemDataRole.UserRole, value)
        elif isinstance(value, dict):
            item.setText(1, "Dictionary")
            item.setText(2, f"{len(value)} items")
            item.setData(2, Qt.ItemDataRole.UserRole, value)
        elif isinstance(value, list):
            item.setText(1, "Array")
            item.setText(2, f"{len(value)} items")
            item.setData(2, Qt.ItemDataRole.UserRole, value)
        else:
            item.setText(1, "Unknown")
            item.setText(2, str(value))
            item.setData(2, Qt.ItemDataRole.UserRole, value)
    
    def edit_item(self, item, column):
        """Edit item value when double-clicked"""
        if column != 2:  # Only allow editing the value column
            return
            
        item_type = item.text(1)
        current_value = item.data(2, Qt.ItemDataRole.UserRole)
        
        # Don't allow editing containers
        if item_type in ("Dictionary", "Array"):
            return
            
        dialog = ValueEditDialog(self, item_type, current_value)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_value = dialog.get_value()
            item.setData(2, Qt.ItemDataRole.UserRole, new_value)
            self._set_item_value(item, new_value)
    
    def get_tree_data(self):
        """Extract data from tree back to dictionary/list format"""
        return self._get_item_data(self.invisibleRootItem())
    
    def _get_item_data(self, parent):
        """Recursively extract data from tree items"""
        child_count = parent.childCount()
        
        # Check if this is a root or if parent is array
        if parent == self.invisibleRootItem():
            # Root level - assume dictionary
            result = OrderedDict()
            for i in range(child_count):
                child = parent.child(i)
                key = child.text(0)
                value = self._get_single_item_data(child)
                result[key] = value
            return result
        
        # Check parent type
        parent_type = parent.text(1) if parent != self.invisibleRootItem() else "Dictionary"
        
        if parent_type == "Array":
            result = []
            for i in range(child_count):
                child = parent.child(i)
                value = self._get_single_item_data(child)
                result.append(value)
            return result
        else:  # Dictionary
            result = OrderedDict()
            for i in range(child_count):
                child = parent.child(i)
                key = child.text(0)
                value = self._get_single_item_data(child)
                result[key] = value
            return result
    
    def _get_single_item_data(self, item):
        """Get data for a single item"""
        item_type = item.text(1)
        
        if item_type in ("Dictionary", "Array"):
            return self._get_item_data(item)
        else:
            return item.data(2, Qt.ItemDataRole.UserRole)


class ValueEditDialog(QDialog):
    """Dialog for editing plist values"""
    
    def __init__(self, parent, value_type, current_value):
        super().__init__(parent)
        self.value_type = value_type
        self.current_value = current_value
        self.setWindowTitle(f"Edit {value_type}")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        label = QLabel(f"Edit {self.value_type} value:")
        layout.addWidget(label)
        
        if self.value_type == "Boolean":
            self.widget = QCheckBox("Value")
            self.widget.setChecked(self.current_value)
        elif self.value_type == "Number":
            self.widget = QSpinBox()
            self.widget.setRange(-2147483648, 2147483647)
            self.widget.setValue(self.current_value)
        elif self.value_type == "String":
            self.widget = QLineEdit()
            self.widget.setText(self.current_value)
        elif self.value_type == "Data":
            self.widget = QTextEdit()
            self.widget.setPlainText(self.current_value.hex())
            self.widget.setMaximumHeight(150)
        else:
            self.widget = QLineEdit()
            self.widget.setText(str(self.current_value))
            
        layout.addWidget(self.widget)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_value(self):
        """Get the edited value"""
        if self.value_type == "Boolean":
            return self.widget.isChecked()
        elif self.value_type == "Number":
            return self.widget.value()
        elif self.value_type == "String":
            return self.widget.text()
        elif self.value_type == "Data":
            try:
                return bytes.fromhex(self.widget.toPlainText().replace(" ", ""))
            except:
                return self.current_value
        else:
            return self.widget.text()


class ConfigEditorPage(QWidget):
    """Config.plist Editor Page with TreeView and OC Snapshot"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("configEditorPage")
        self.controller = parent
        self.current_file = None
        self.plist_data = None
        self.snapshot_data = None
        self.setup_ui()
        self.load_snapshot_data()
        
    def setup_ui(self):
        """Setup the config editor page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['xxlarge'], SPACING['xlarge'],
                                  SPACING['xxlarge'], SPACING['xlarge'])
        layout.setSpacing(SPACING['large'])
        
        # Title section
        title_label = SubtitleLabel("Config.plist Editor")
        layout.addWidget(title_label)
        
        subtitle_label = BodyLabel("Load, edit, and manage your OpenCore configuration")
        subtitle_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(SPACING['medium'])
        
        # Toolbar card
        toolbar_card = CardWidget()
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(SPACING['large'], SPACING['medium'],
                                         SPACING['large'], SPACING['medium'])
        
        # File operations
        self.load_btn = PushButton(FluentIcon.FOLDER, "Load config.plist")
        self.load_btn.clicked.connect(self.load_config)
        toolbar_layout.addWidget(self.load_btn)
        
        self.save_btn = PushButton(FluentIcon.SAVE, "Save")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_btn)
        
        self.save_as_btn = PushButton(FluentIcon.SAVE_AS, "Save As...")
        self.save_as_btn.clicked.connect(self.save_config_as)
        self.save_as_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_as_btn)
        
        toolbar_layout.addSpacing(SPACING['medium'])
        
        # OC Snapshot operations
        self.snapshot_btn = PrimaryPushButton(FluentIcon.SYNC, "OC Snapshot")
        self.snapshot_btn.clicked.connect(self.oc_snapshot)
        self.snapshot_btn.setEnabled(False)
        toolbar_layout.addWidget(self.snapshot_btn)
        
        self.clean_snapshot_btn = PushButton(FluentIcon.DELETE, "OC Clean Snapshot")
        self.clean_snapshot_btn.clicked.connect(self.oc_clean_snapshot)
        self.clean_snapshot_btn.setEnabled(False)
        toolbar_layout.addWidget(self.clean_snapshot_btn)
        
        toolbar_layout.addStretch()
        
        # Current file label
        self.file_label = BodyLabel("No file loaded")
        self.file_label.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        toolbar_layout.addWidget(self.file_label)
        
        layout.addWidget(toolbar_card)
        
        # Tree view card
        tree_card = CardWidget()
        tree_layout = QVBoxLayout(tree_card)
        tree_layout.setContentsMargins(SPACING['large'], SPACING['large'],
                                      SPACING['large'], SPACING['large'])
        
        tree_title = StrongBodyLabel("Configuration Tree")
        tree_layout.addWidget(tree_title)
        
        help_label = BodyLabel("Double-click values to edit • OC Snapshot scans your OC folder and updates ACPI/Kexts/Drivers/Tools")
        help_label.setStyleSheet(f"color: {COLORS['text_tertiary']}; font-size: 12px;")
        tree_layout.addWidget(help_label)
        
        tree_layout.addSpacing(SPACING['small'])
        
        # Tree widget
        self.tree = PlistTreeWidget()
        tree_layout.addWidget(self.tree)
        
        layout.addWidget(tree_card, 1)
        
    def load_snapshot_data(self):
        """Load snapshot.plist data for OC version detection"""
        try:
            # Copy snapshot.plist from ProperTree if not exists
            snapshot_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "snapshot.plist"
            )
            
            if not os.path.exists(snapshot_path):
                # Try to find it in the current directory structure
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), "snapshot.plist"),
                    os.path.join(os.path.dirname(__file__), "..", "snapshot.plist"),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        snapshot_path = path
                        break
            
            if os.path.exists(snapshot_path):
                with open(snapshot_path, 'rb') as f:
                    self.snapshot_data = plistlib.load(f)
            else:
                self.snapshot_data = None
                print("Warning: snapshot.plist not found. OC version detection will be limited.")
        except Exception as e:
            print(f"Error loading snapshot.plist: {e}")
            self.snapshot_data = None
    
    def load_config(self):
        """Load a config.plist file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select config.plist",
            "",
            "Plist Files (*.plist);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'rb') as f:
                self.plist_data = plistlib.load(f)
            
            self.current_file = file_path
            self.tree.populate_tree(self.plist_data)
            self.file_label.setText(f"Loaded: {os.path.basename(file_path)}")
            
            # Enable buttons
            self.save_btn.setEnabled(True)
            self.save_as_btn.setEnabled(True)
            self.snapshot_btn.setEnabled(True)
            self.clean_snapshot_btn.setEnabled(True)
            
            InfoBar.success(
                title='Success',
                content=f'Loaded {os.path.basename(file_path)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            
        except Exception as e:
            MessageBox(
                "Error Loading File",
                f"Failed to load config.plist:\n{str(e)}",
                self
            ).exec()
    
    def save_config(self):
        """Save the current config.plist"""
        if not self.current_file:
            self.save_config_as()
            return
            
        try:
            # Get data from tree
            data = self.tree.get_tree_data()
            
            # Save to file
            with open(self.current_file, 'wb') as f:
                plistlib.dump(data, f, sort_keys=False)
            
            InfoBar.success(
                title='Saved',
                content=f'Saved {os.path.basename(self.current_file)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            
        except Exception as e:
            MessageBox(
                "Error Saving File",
                f"Failed to save config.plist:\n{str(e)}",
                self
            ).exec()
    
    def save_config_as(self):
        """Save the config.plist to a new file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save config.plist As",
            "config.plist",
            "Plist Files (*.plist);;All Files (*)"
        )
        
        if not file_path:
            return
            
        self.current_file = file_path
        self.save_config()
        self.file_label.setText(f"Loaded: {os.path.basename(file_path)}")
    
    def oc_snapshot(self):
        """Perform OC Snapshot"""
        self._perform_snapshot(clean=False)
    
    def oc_clean_snapshot(self):
        """Perform OC Clean Snapshot"""
        self._perform_snapshot(clean=True)
    
    def _perform_snapshot(self, clean=False):
        """Perform OC Snapshot operation"""
        if not self.plist_data:
            MessageBox(
                "No Config Loaded",
                "Please load a config.plist file first.",
                self
            ).exec()
            return
        
        # Get target directory from current file's directory
        target_dir = os.path.dirname(self.current_file) if self.current_file else None
        
        # Prompt for OC folder
        oc_folder = QFileDialog.getExistingDirectory(
            self,
            "Select OC Folder",
            target_dir or ""
        )
        
        if not oc_folder:
            return
        
        # Verify folder structure
        oc_acpi = os.path.join(oc_folder, "ACPI")
        oc_drivers = os.path.join(oc_folder, "Drivers")
        oc_kexts = os.path.join(oc_folder, "Kexts")
        oc_tools = os.path.join(oc_folder, "Tools")
        
        missing = []
        if not os.path.isdir(oc_acpi):
            missing.append("ACPI")
        if not os.path.isdir(oc_drivers):
            missing.append("Drivers")
        if not os.path.isdir(oc_kexts):
            missing.append("Kexts")
        
        if missing:
            # Try OC subfolder
            oc_folder_alt = os.path.join(oc_folder, "OC")
            if os.path.isdir(oc_folder_alt):
                oc_acpi = os.path.join(oc_folder_alt, "ACPI")
                oc_drivers = os.path.join(oc_folder_alt, "Drivers")
                oc_kexts = os.path.join(oc_folder_alt, "Kexts")
                oc_tools = os.path.join(oc_folder_alt, "Tools")
                
                missing = []
                if not os.path.isdir(oc_acpi):
                    missing.append("ACPI")
                if not os.path.isdir(oc_drivers):
                    missing.append("Drivers")
                if not os.path.isdir(oc_kexts):
                    missing.append("Kexts")
                    
                if not missing:
                    oc_folder = oc_folder_alt
        
        if missing:
            MessageBox(
                "Incorrect OC Folder Structure",
                f"The following required folders do not exist:\n\n{', '.join(missing)}\n\nPlease make sure you're selecting a valid OC folder.",
                self
            ).exec()
            return
        
        try:
            # Get current tree data
            tree_data = self.tree.get_tree_data()
            
            # Perform snapshot operations
            self._snapshot_acpi(tree_data, oc_acpi, clean)
            self._snapshot_kexts(tree_data, oc_kexts, clean)
            self._snapshot_drivers(tree_data, oc_drivers, clean)
            self._snapshot_tools(tree_data, oc_tools, clean)
            
            # Update tree
            self.tree.populate_tree(tree_data)
            self.plist_data = tree_data
            
            InfoBar.success(
                title='Snapshot Complete',
                content='OC Snapshot completed successfully',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            MessageBox(
                "Snapshot Error",
                f"Error during OC Snapshot:\n{str(e)}",
                self
            ).exec()
    
    def _snapshot_acpi(self, tree_data, oc_acpi, clean):
        """Snapshot ACPI folder"""
        # Ensure ACPI->Add exists
        if "ACPI" not in tree_data:
            tree_data["ACPI"] = OrderedDict()
        if "Add" not in tree_data["ACPI"]:
            tree_data["ACPI"]["Add"] = []
        
        # Scan ACPI folder
        new_acpi = []
        for root, dirs, files in os.walk(oc_acpi):
            for name in files:
                if not name.startswith(".") and name.lower().endswith((".aml", ".bin")):
                    rel_path = os.path.relpath(os.path.join(root, name), oc_acpi)
                    rel_path = rel_path.replace("\\", "/")
                    new_acpi.append(rel_path)
        
        # Build new ACPI list
        add = [] if clean else tree_data["ACPI"]["Add"]
        existing_paths = [x.get("Path", "").lower() for x in add if isinstance(x, dict)]
        
        for aml in sorted(new_acpi, key=lambda x: x.lower()):
            if aml.lower() not in existing_paths:
                # Add new entry
                new_entry = OrderedDict([
                    ("Comment", os.path.basename(aml)),
                    ("Enabled", True),
                    ("Path", aml)
                ])
                add.append(new_entry)
        
        # Remove entries that don't exist
        new_add = []
        new_acpi_lower = [x.lower() for x in new_acpi]
        for entry in add:
            if isinstance(entry, dict) and entry.get("Path", "").lower() in new_acpi_lower:
                new_add.append(entry)
        
        tree_data["ACPI"]["Add"] = new_add
    
    def _snapshot_kexts(self, tree_data, oc_kexts, clean):
        """Snapshot Kexts folder"""
        # Ensure Kernel->Add exists
        if "Kernel" not in tree_data:
            tree_data["Kernel"] = OrderedDict()
        if "Add" not in tree_data["Kernel"]:
            tree_data["Kernel"]["Add"] = []
        
        # Scan kexts
        kext_list = []
        for root, dirs, files in os.walk(oc_kexts):
            for name in sorted(dirs, key=lambda x: x.lower()):
                if name.startswith(".") or not name.lower().endswith(".kext"):
                    continue
                
                kext_path = os.path.join(root, name)
                rel_path = os.path.relpath(kext_path, oc_kexts).replace("\\", "/")
                
                # Find Info.plist
                info_plist_path = None
                for kroot, kdirs, kfiles in os.walk(kext_path):
                    if "Info.plist" in kfiles:
                        info_plist_path = os.path.join(kroot, "Info.plist")
                        break
                
                if not info_plist_path:
                    continue
                
                try:
                    with open(info_plist_path, 'rb') as f:
                        info_plist = plistlib.load(f)
                    
                    if "CFBundleIdentifier" not in info_plist:
                        continue
                    
                    plist_rel_path = os.path.relpath(info_plist_path, kext_path).replace("\\", "/")
                    
                    # Find executable
                    exec_path = ""
                    if "CFBundleExecutable" in info_plist:
                        exec_name = info_plist["CFBundleExecutable"]
                        exec_full = os.path.join(kext_path, "Contents", "MacOS", exec_name)
                        if os.path.exists(exec_full) and os.path.getsize(exec_full) > 0:
                            exec_path = f"Contents/MacOS/{exec_name}"
                    
                    kext_entry = OrderedDict([
                        ("Arch", "Any"),
                        ("BundlePath", rel_path),
                        ("Comment", name),
                        ("Enabled", True),
                        ("ExecutablePath", exec_path),
                        ("MaxKernel", ""),
                        ("MinKernel", ""),
                        ("PlistPath", plist_rel_path)
                    ])
                    
                    kext_list.append(kext_entry)
                    
                except Exception as e:
                    print(f"Error processing kext {name}: {e}")
                    continue
        
        # Build new kext list
        add = [] if clean else tree_data["Kernel"]["Add"]
        existing_bundles = [x.get("BundlePath", "").lower() for x in add if isinstance(x, dict)]
        
        for kext in kext_list:
            if kext["BundlePath"].lower() not in existing_bundles:
                add.append(kext)
        
        # Remove entries that don't exist
        new_add = []
        kext_bundles = [k["BundlePath"].lower() for k in kext_list]
        for entry in add:
            if isinstance(entry, dict) and entry.get("BundlePath", "").lower() in kext_bundles:
                # Update paths if needed
                matching_kext = next((k for k in kext_list if k["BundlePath"].lower() == entry.get("BundlePath", "").lower()), None)
                if matching_kext:
                    if "ExecutablePath" in matching_kext:
                        entry["ExecutablePath"] = matching_kext["ExecutablePath"]
                    if "PlistPath" in matching_kext:
                        entry["PlistPath"] = matching_kext["PlistPath"]
                new_add.append(entry)
        
        tree_data["Kernel"]["Add"] = new_add
    
    def _snapshot_drivers(self, tree_data, oc_drivers, clean):
        """Snapshot Drivers folder"""
        # Ensure UEFI->Drivers exists
        if "UEFI" not in tree_data:
            tree_data["UEFI"] = OrderedDict()
        if "Drivers" not in tree_data["UEFI"]:
            tree_data["UEFI"]["Drivers"] = []
        
        # Scan drivers
        new_drivers = []
        for root, dirs, files in os.walk(oc_drivers):
            for name in files:
                if not name.startswith(".") and name.lower().endswith(".efi"):
                    rel_path = os.path.relpath(os.path.join(root, name), oc_drivers)
                    rel_path = rel_path.replace("\\", "/")
                    new_drivers.append(rel_path)
        
        # Build new driver list
        drivers = [] if clean else tree_data["UEFI"]["Drivers"]
        existing_paths = [x.get("Path", "").lower() if isinstance(x, dict) else x.lower() for x in drivers]
        
        for driver in sorted(new_drivers, key=lambda x: x.lower()):
            if driver.lower() not in existing_paths:
                # Check if we need dict format (OC 0.6.0+) or string format
                if drivers and isinstance(drivers[0], dict):
                    new_entry = OrderedDict([
                        ("Arguments", ""),
                        ("Comment", os.path.basename(driver)),
                        ("Enabled", True),
                        ("LoadEarly", False),
                        ("Path", driver)
                    ])
                    drivers.append(new_entry)
                else:
                    drivers.append(driver)
        
        # Remove entries that don't exist
        new_drivers_lower = [x.lower() for x in new_drivers]
        new_list = []
        for entry in drivers:
            path = entry.get("Path", "").lower() if isinstance(entry, dict) else entry.lower()
            if path in new_drivers_lower:
                new_list.append(entry)
        
        tree_data["UEFI"]["Drivers"] = new_list
    
    def _snapshot_tools(self, tree_data, oc_tools, clean):
        """Snapshot Tools folder"""
        if not os.path.isdir(oc_tools):
            return  # Tools folder is optional
        
        # Ensure Misc->Tools exists
        if "Misc" not in tree_data:
            tree_data["Misc"] = OrderedDict()
        if "Tools" not in tree_data["Misc"]:
            tree_data["Misc"]["Tools"] = []
        
        # Scan tools
        new_tools = []
        for root, dirs, files in os.walk(oc_tools):
            for name in files:
                if not name.startswith(".") and name.lower().endswith(".efi"):
                    rel_path = os.path.relpath(os.path.join(root, name), oc_tools)
                    rel_path = rel_path.replace("\\", "/")
                    new_tools.append(rel_path)
        
        # Build new tools list
        tools = [] if clean else tree_data["Misc"]["Tools"]
        existing_paths = [x.get("Path", "").lower() for x in tools if isinstance(x, dict)]
        
        for tool in sorted(new_tools, key=lambda x: x.lower()):
            if tool.lower() not in existing_paths:
                new_entry = OrderedDict([
                    ("Arguments", ""),
                    ("Auxiliary", True),
                    ("Comment", os.path.basename(tool)),
                    ("Enabled", True),
                    ("Flavour", "Auto"),
                    ("FullNvramAccess", False),
                    ("Path", tool),
                    ("RealPath", False),
                    ("TextMode", False)
                ])
                tools.append(new_entry)
        
        # Remove entries that don't exist
        new_tools_lower = [x.lower() for x in new_tools]
        new_list = []
        for entry in tools:
            if isinstance(entry, dict) and entry.get("Path", "").lower() in new_tools_lower:
                new_list.append(entry)
        
        tree_data["Misc"]["Tools"] = new_list
