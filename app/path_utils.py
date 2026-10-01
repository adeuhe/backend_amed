import os
import sys

def get_resource_path(relative_path: str = "") -> str:
    """
    Returns absolute path to resource, fully compatible with PyInstaller bundle (_MEIPASS)
    and standard Python development environment.
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller compiled executable
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # Running in standard Python development mode
        # Path to root folder (parent of app directory)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if not relative_path:
        return base_path

    target = os.path.join(base_path, relative_path)
    if not os.path.exists(target) and getattr(sys, 'frozen', False):
        # Fallback to directory next to the .exe binary
        exe_dir_target = os.path.join(os.path.dirname(sys.executable), relative_path)
        if os.path.exists(exe_dir_target):
            return exe_dir_target

    return target

def get_config_env_path() -> str:
    """
    Returns path to .env file.
    Prioritizes external .env placed next to the .exe binary so users can modify port/database settings dynamically.
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        exe_env = os.path.join(exe_dir, ".env")
        if os.path.exists(exe_env):
            return exe_env
        bundled_env = os.path.join(getattr(sys, '_MEIPASS', exe_dir), ".env")
        if os.path.exists(bundled_env):
            return bundled_env
        return exe_env
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, ".env")

