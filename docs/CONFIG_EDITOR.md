# Config.plist Editor

A powerful TreeView-based editor for OpenCore config.plist files with OC Snapshot and validation features.

## Features

### 1. Interactive TreeView Editor
- **Hierarchical Display**: View your config.plist in a clear, organized tree structure
- **Type-aware Editing**: Edit values with appropriate controls:
  - Boolean: Checkbox
  - Number: Spin box with proper range
  - String: Text input
  - Data: Hexadecimal editor
- **Double-click to Edit**: Quick and intuitive editing workflow
- **Real-time Updates**: Changes are immediately reflected in the tree

### 2. OC Snapshot
Automatically scan your OpenCore EFI folder and update config.plist with discovered files:

#### What OC Snapshot Does:
- **Scans ACPI folder** for `.aml` and `.bin` files
- **Scans Kexts folder** and parses `Info.plist` files
  - Automatically detects ExecutablePath
  - Handles nested kext structures
  - Validates kext configuration
- **Scans Drivers folder** for `.efi` files
- **Scans Tools folder** for `.efi` files
- **Preserves existing entries** (doesn't delete manually added configurations)
- **Updates paths** if files have been moved or renamed

#### Two Snapshot Modes:
1. **OC Snapshot**: Adds new entries while preserving existing ones
2. **OC Clean Snapshot**: Removes all existing entries and rebuilds from scratch

#### Usage:
1. Load a config.plist file
2. Click "OC Snapshot" or "OC Clean Snapshot"
3. Select your OC folder (the one containing ACPI, Kexts, Drivers, Tools subdirectories)
4. Review the updated configuration
5. Save the file

### 3. Validation
Comprehensive validation checks to ensure your config.plist is properly configured:

#### Validation Checks:

**Path Length Validation**
- Ensures all paths are under 128 characters (OC_STORAGE_SAFE_PATH_MAX)
- Checks ACPI, Kext, Driver, and Tool paths
- Special validation for kext combined paths (BundlePath + ExecutablePath/PlistPath)

**Structure Validation**
- Verifies required sections exist:
  - ACPI, Booter, DeviceProperties, Kernel, Misc, NVRAM, PlatformInfo, UEFI
- Checks for recommended subsections
- Warns about missing or incomplete sections

**Duplicate Detection**
- Identifies duplicate ACPI paths
- Identifies duplicate Kext bundle paths
- Helps prevent conflicts and boot issues

**Kext Dependency Checking**
- Validates load order for common kexts
- Checks dependencies like:
  - Lilu.kext dependencies: WhateverGreen, AppleALC, etc.
  - VirtualSMC.kext dependencies: SMCProcessor, SMCBatteryManager, etc.
- Warns if dependencies are loaded in wrong order

#### Validation Results:
- **Errors**: Critical issues that may prevent booting
- **Warnings**: Potential issues or improvements

### 4. File Operations
- **Load**: Open any config.plist file
- **Save**: Save changes to the current file
- **Save As**: Save to a new file location

## How to Use

### Basic Workflow

1. **Load a config.plist**
   - Click "Load config.plist" button
   - Select your OpenCore config.plist file
   - The tree will populate with your configuration

2. **Edit Values**
   - Double-click any value in the "Value" column
   - Edit using the appropriate dialog
   - Changes are saved to the tree immediately

3. **Run OC Snapshot** (Optional but Recommended)
   - Click "OC Snapshot" button
   - Select your OC folder (typically at `EFI/OC/`)
   - Review the updated entries
   - The snapshot will:
     - Add any missing ACPI files
     - Add any missing Kexts with proper paths
     - Add any missing Drivers
     - Add any missing Tools
     - Remove entries for files that no longer exist

4. **Validate Configuration**
   - Click "Validate" button
   - Review any errors or warnings
   - Fix issues as needed

5. **Save Your Changes**
   - Click "Save" to save to the current file
   - Or "Save As" to save to a new location

### Advanced Usage

#### Clean Snapshot Workflow
Use this when you want to completely rebuild your config from scratch:

1. Load your config.plist
2. Click "OC Clean Snapshot"
3. Select your OC folder
4. All ACPI/Kext/Driver/Tool entries will be cleared and rebuilt
5. Review and save

#### Manual Editing
You can manually edit values in the tree:

1. Navigate to the value you want to edit
2. Double-click in the "Value" column
3. Edit in the dialog that appears
4. Click OK to save changes

## Best Practices

1. **Backup First**: Always backup your config.plist before making changes
2. **Validate Often**: Run validation after making significant changes
3. **Use OC Snapshot**: Let the tool handle file paths to avoid typos
4. **Check Dependencies**: Pay attention to kext dependency warnings
5. **Test Your Changes**: Always test your EFI on the target system

## Tips

- **Path Length**: Keep your file and folder names short to avoid exceeding the 128 character limit
- **Kext Order**: The order in the tree matters for kexts with dependencies
- **Clean Snapshot**: Use clean snapshot when reorganizing your EFI folder structure
- **Validation**: Run validation before closing the editor to catch issues early

## Limitations

- Cannot add/remove dictionary keys or array items (planned for future release)
- Cannot reorder entries in the tree (use manual editing for now)
- Kext dependency checking covers common kexts only
- OpenCore version detection requires snapshot.plist (included)

## Technical Details

### Based on ProperTree
The OC Snapshot functionality is based on [ProperTree](https://github.com/corpnewt/ProperTree) by CorpNewt, 
the de-facto standard plist editor for OpenCore configurations.

### Path Length Constant
The path length validation uses `OC_STORAGE_SAFE_PATH_MAX = 128` from OpenCorePkg 
(`Include/Acidanthera/Library/OcStorageLib.h`).

### File Format
The editor preserves plist formatting and uses OrderedDict to maintain key order when saving.

## Troubleshooting

**Q: OC Snapshot doesn't find my files**
- Make sure you selected the correct OC folder (should contain ACPI, Kexts, Drivers subdirectories)
- Try selecting the parent folder if you selected EFI/OC directly

**Q: Validation shows path too long errors**
- Shorten your file names or folder structure
- Consider flattening your kext directory structure

**Q: Kext dependency warnings appear**
- Check the load order in config.plist
- Make sure parent kexts (like Lilu.kext, VirtualSMC.kext) are loaded before their dependencies

**Q: Can't edit certain values**
- Dictionary and Array containers cannot be edited directly
- Edit their child values instead

## Future Enhancements

Planned features for future releases:
- Add/remove dictionary keys and array items
- Drag-and-drop reordering in tree
- Expanded kext dependency database
- OpenCore version-specific validation
- Undo/redo functionality
- Search/filter in tree
- Export validation reports
