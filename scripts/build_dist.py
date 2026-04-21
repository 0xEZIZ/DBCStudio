import PyInstaller.__main__
import os
import shutil

def build():
    # Application Name
    app_name = "CAN_DBC_Tool"
    
    # Path to main script
    script_path = "main.py"
    
    # Icon Path
    icon_path = os.path.join("assets", "app_icon.ico")
    
    print(f"[*] Starting build for {app_name}...")
    
    # PyInstaller arguments
    args = [
        script_path,
        '--name=%s' % app_name,
        '--onedir',                # Folder mode as requested
        '--console',               # Keep console visible as requested
        '--icon=%s' % icon_path,   # Set custom icon
        '--noconfirm',             # Overwrite existing dist
        
        # Hidden imports for hardware and other libs
        '--hidden-import=can.interfaces.ixxat',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtMultimedia',
        '--hidden-import=PyQt5.QtMultimediaWidgets',
        
        # Collect all from python-can to ensure backends are included
        '--collect-all=can',
        '--collect-all=pyqtgraph',
        
        # Metadata
        '--clean',
    ]
    
    # Execute PyInstaller
    PyInstaller.__main__.run(args)
    
    print(f"\n[+] Build complete! Check the 'dist/{app_name}' folder.")

if __name__ == "__main__":
    build()
