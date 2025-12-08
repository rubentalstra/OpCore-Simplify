"""
Icon system for OpCore Simplify GUI using qfluentwidgets.
Provides a centralized mapping system for FluentIcon enumeration.
"""

from typing import Final
from qfluentwidgets import FluentIcon

# Icon mapping for backward compatibility and easy reference
ICON_MAP: Final[dict[str, FluentIcon]] = {
    'upload': FluentIcon.FOLDER_ADD,
    'settings': FluentIcon.SETTING,
    'search': FluentIcon.SEARCH,
    'wrench': FluentIcon.CONSTRACT,
    'hammer': FluentIcon.DEVELOPER_TOOLS,
    'wifi': FluentIcon.WIFI,
    'clipboard': FluentIcon.DOCUMENT,
    'check': FluentIcon.ACCEPT,
    'cross': FluentIcon.CLOSE,
    'warning': FluentIcon.WARNING,
    'info': FluentIcon.INFO,
    'lightning': FluentIcon.LIGHTNING,
    'folder': FluentIcon.FOLDER,
    'save': FluentIcon.SAVE,
    'download': FluentIcon.DOWNLOAD,
    'refresh': FluentIcon.SYNC,
    'delete': FluentIcon.DELETE,
    'add': FluentIcon.ADD,
    'remove': FluentIcon.REMOVE,
    'edit': FluentIcon.EDIT,
    'copy': FluentIcon.COPY,
    'cut': FluentIcon.CUT,
    'paste': FluentIcon.PASTE,
}


class Icons:
    """Icon provider using qfluentwidgets FluentIcon enumeration."""

    @staticmethod
    def get_icon(name: str) -> FluentIcon:
        """
        Get FluentIcon by name.
        
        Args:
            name: String identifier for the icon
            
        Returns:
            FluentIcon: The corresponding FluentIcon, or INFO if not found
        """
        return ICON_MAP.get(name, FluentIcon.INFO)
