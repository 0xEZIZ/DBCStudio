import os
from PIL import Image

def convert_png_to_ico(png_path, ico_path):
    print(f"[*] Converting {png_path} to {ico_path}...")
    img = Image.open(png_path)
    # Resize and save as ICO with multiple sizes for Windows
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"[+] Icon saved to {ico_path}")

if __name__ == "__main__":
    assets_dir = "assets"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    source_png = r"C:\Users\Керим\.gemini\antigravity\brain\d9e14e26-3f65-4441-95cf-e891f35714f1\can_bus_tool_icon_1776411001909.png"
    target_ico = os.path.join(assets_dir, "app_icon.ico")
    
    try:
        convert_png_to_ico(source_png, target_ico)
    except Exception as e:
        print(f"[!] Error: {e}")
