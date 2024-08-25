import os
import glob
import shutil
import zipfile
import plistlib
from rich.table import Table
from rich.console import Console

def extract_ipa(path_to_ipa: str, console: Console) -> str:
    extract_dir = "./tmp/extracted/"
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    with console.status(f"Extracting iPA {path_to_ipa}", spinner="dots"):
        with zipfile.ZipFile(path_to_ipa, 'r') as zipf:
            zipf.extractall(extract_dir)
    
    return extract_dir

def get_app_properties(extracted_dir: str, show_table: bool, console: Console) -> dict:
    console.log("Reading Info.plist...")
    info_plist = glob.glob(os.path.join(extracted_dir, "Payload", "*.app", "Info.plist"))
    if not info_plist:
        console.log("[bold red] Malformed iPA: Info.plist or .app directory not found")
        return None
    info_plist = info_plist[0]
    with open(info_plist, "rb") as plist:
        plist_data = plistlib.load(plist)
        if show_table:
            table = Table(title=plist_data.get('CFBundleDisplayName'))
            table.add_column("Property")
            table.add_column("Value")
            table.add_row("Name", plist_data.get("CFBundleName"))
            table.add_row("Display Name", plist_data.get("CFBundleDisplayName"))
            table.add_row("Identifier", plist_data.get("CFBundleIdentifier"))
            table.add_row("Version", plist_data.get("CFBundleVersion"))
            table.add_row("Target iOS", plist_data.get("MinimumOSVersion"))
            console.log(table)
        return plist_data