import os
import glob
import shutil
import hashlib
import argparse
import configparser
import macholib.MachO
import macholib.mach_o
from rich.table import Table
from rich.console import Console
import utils.common

def sort_and_label(args: argparse, path_to_ipa: str, output_path: str, console: Console):
    if path_to_ipa is None:
        return
    try:
        extracted_ipa = utils.common.extract_ipa(path_to_ipa, console)
        properties = utils.common.get_app_properties(extracted_ipa, console)
        executable = glob.glob(os.path.join(extracted_ipa, 'Payload', '*.app', properties.get("CFBundleExecutable")))[0]
        
        cryptid = get_cryptid(executable)
        architecture = get_architecture(executable)

        print_table(properties, cryptid, architecture, console)

        if properties.get('CFBundleIdentifier') == None or properties.get("CFBundleVersion") == None or properties.get("MinimumOSVersion") == None:
            console.log(f"[bold red]An error occurred sorting {path_to_ipa}")
            return
        
        if properties.get('CFBundleDisplayName') == None:
            properties['CFBundleDisplayName'] = properties["CFBundleName"]

        obscura_filename = f"{properties.get('CFBundleDisplayName')}-({properties.get('CFBundleIdentifier')})-{properties.get('CFBundleVersion')}-(iOS_{properties.get('MinimumOSVersion')})-{hashlib.md5(open(path_to_ipa,'rb').read()).hexdigest()}.ipa"
        console.log(f"Obscura-format filename: \n{obscura_filename}")

        ios_ver = str(properties.get("MinimumOSVersion")).split(".")[0]

        if not cryptid:
            path_tree = os.path.join(output_path, "Decrypted", architecture, f"iOS {ios_ver}", properties.get("CFBundleIdentifier"))
        else:
            path_tree = os.path.join(output_path, "Encrypted", architecture, f"iOS {ios_ver}", properties.get("CFBundleIdentifier"))

        os.makedirs(path_tree, exist_ok=True)
        if os.path.exists(os.path.join(path_tree, obscura_filename)):
            console.log("IPA is a duplicate, won't move...")
        else:
            shutil.move(path_to_ipa, os.path.join(path_tree, obscura_filename))
    except Exception as e:
        console.log(f"[bold red]An error occurred sorting {path_to_ipa}: {e}")
        if args.debug: console.print_exception(show_locals=True)
    
def get_cryptid(executable: str) -> bool:
    macho = macholib.MachO.MachO(executable)

    for header in macho.headers:
        load_commands = header.commands
        for load_command in load_commands:
            if isinstance(load_command[1], macholib.mach_o.encryption_info_command):
                if load_command[1].cryptid == 0:
                    return False
            if isinstance(load_command[1], macholib.mach_o.encryption_info_command_64):
                if load_command[1].cryptid == 0:
                    return False
    return True

def get_architecture(filename: str) -> str:
    # thanks to https://iphonedev.wiki/Mach-O_File_Format#CPU_Type
    macho = macholib.MachO.MachO(filename)
    supports_32 = False
    supports_64 = False

    for header in macho.headers:
        if header.header.cputype == 16777228: # ARM64
            supports_64 = True
        if header.header.cputype == 12: # ARMv6, ARMv7 and ARMv7s(hopefully ?)
            supports_32 = True
            
    if supports_32 and supports_64:
        return "Universal"
    elif supports_64:
        return "64-bit"
    else:
        return "32-bit"

def print_table(properties: dict, crypted: bool, architecture: str, console: Console):
    table = Table(title=properties.get('CFBundleDisplayName'))
    table.add_column("Property")
    table.add_column("Value")
    table.add_row("Name", properties.get("CFBundleName"))
    table.add_row("Display Name", properties.get("CFBundleDisplayName"))
    table.add_row("Identifier", properties.get("CFBundleIdentifier"))
    table.add_row("Version", properties.get("CFBundleVersion"))
    table.add_row("Target iOS", properties.get("MinimumOSVersion"))
    table.add_row("Architecture", architecture)
    if crypted:
        table.add_row("Encrypted", "[bold red]YES")
    else:
        table.add_row("Encrypted", "[bold green]NO")
    console.log(table)

def sort_and_label_batch(args: argparse.ArgumentParser, config: configparser.ConfigParser, console: Console):
    dupe_count = 0
    total = 0
    error_count = 0
    for path, _, files in os.walk(args.input_path):
        for file in files:
            total += 1
            try:
                sort_and_label(args, os.path.join(path, file), args.output_path, console)
            except Exception as e:
                error_count += 1
                console.log(f"[bold red] Error occurred while sorting {file}: {e}")
    console.print(f"{total} IPAs sorted and saved.")
    console.print(f"There were {error_count} errored iPAs and {dupe_count} duplicates in this batch.")