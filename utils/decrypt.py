import os
import time
import random
import shutil
import argparse
import subprocess
import configparser
import paramiko
from rich.console import Console
from rich.progress import track
import utils.sort
import utils.common

def connect_ssh(config: configparser.ConfigParser, console: Console):
    with console.status(f"\nEstablishing SSH connection with {dict(config['decryption-device'])['ssh_host']}:{dict(config['decryption-device'])['ssh_port']}", spinner="dots"):
        console.log(f"\tUsing credentials {dict(config['decryption-device'])['ssh_username']}:{dict(config['decryption-device'])['ssh_password']}")

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(dict(config['decryption-device'])['ssh_host'], port=dict(config['decryption-device'])['ssh_port'], username=dict(config['decryption-device'])['ssh_username'], password=dict(config['decryption-device'])['ssh_password'])
        
        if ssh_client:
            console.log("SSH connection successful")
    return ssh_client

def install_ipa(path_to_ipa: str, ssh_client: paramiko.SSHClient, properties: dict, console: Console) -> None:
    tmp_ipa_path = f"./tmp/{str(random.randint(111111,999999))}.ipa" # ideviceinstaller hates files with unicode names for some reason

    shutil.copy(path_to_ipa, tmp_ipa_path)

    console.log("\t[bold yellow] Sending action LOCKSCREEN.DISMISS")
    ssh_client.exec_command("activator send libactivator.lockscreen.dismiss")

    with console.status(f"Installing {properties.get('CFBundleIdentifier')}", spinner="arrow3"):
        subprocess.run(
            f'./libimobiledevice/ideviceinstaller.exe install "{tmp_ipa_path}"' if os.name == 'nt' else f'ideviceinstaller install "{tmp_ipa_path}"',
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        os.remove(tmp_ipa_path)

def get_package_number(clutch_output: str, properties: dict) -> str:
    package_number = ""

    for line in clutch_output.splitlines():
        if properties.get("CFBundleIdentifier") in line:
            package_number = line.split(":")[0]
            break
    return package_number

def decrypt_app(args: argparse.ArgumentParser, config: configparser.ConfigParser, properties: dict, ssh_client: paramiko.SSHClient, package_number: str, console: Console):
    for attempt in track(range(args.attempts), description=f"Attempting to decrypt {properties.get('CFBundleIdentifier')}", console=console):
        if not args.no_bypass:
            bypass(config, properties, ssh_client, console)

        console.log(f"Attempt ({attempt+1}/{args.attempts})")

        _, output, errput = ssh_client.exec_command(f"clutch -d {package_number}")
        print(output.read().decode('utf-8'))
        print(errput.read().decode('utf-8'))

        if output.channel.recv_exit_status() == 0:
            return True
        else:
            console.log(f"[bold red] Decryption failed with code {output.channel.recv_exit_status()}, retrying...")

            console.log("\t[bold yellow]Sending action SYSTEM.HOMEBUTTON")
            ssh_client.exec_command("activator send libactivator.system.homebutton")

            time.sleep(2)

            console.log(f"\t[bold yellow]Sending command \'killall {properties.get('CFBundleExecutable')}\'")
            ssh_client.exec_command(f"killall {properties.get('CFBundleExecutable')}")

            time.sleep(1)
    console.log(f"[bold red]Decryption attempts exausted for {properties.get('CFBundleIdentifier')}")
    return False

def bypass(config: configparser.ConfigParser, properties: dict, ssh_client: paramiko.SSHClient, console: Console):
    console.log("\t[bold yellow]Sending action LOCKSCREEN.DISMISS")
    ssh_client.exec_command("activator send libactivator.lockscreen.dismiss")

    time.sleep(float(dict(config['bypass']).get('springboard_to_launch')))

    console.log(f"\t[bold yellow]Sending action START {properties.get('CFBundleIdentifier')}")
    ssh_client.exec_command(f"activator send {properties['CFBundleIdentifier']}")

    time.sleep(float(dict(config['bypass']).get('app_to_lock')))

    console.log("\t[bold yellow]Sending action LOCKSCREEN.SHOW")
    ssh_client.exec_command("activator send libactivator.lockscreen.show")
    console.log("\t[bold yellow]Sending action LOCKSCREEN.SHOW")
    ssh_client.exec_command("activator send libactivator.lockscreen.show")
    console.log("\t[bold yellow]Sending action Locksreen.SHOW")
    ssh_client.exec_command("activator send libactivator.lockscreen.show")

    time.sleep(float(dict(config['bypass']).get('lock_to_app')))

    console.log("\t[bold yellow]Sending action LOCKSCREEN.DISMISS")
    ssh_client.exec_command("activator send libactivator.lockscreen.dismiss")

    time.sleep(float(dict(config['bypass']).get('app_ensure_open')))

    console.log("\t[bold yellow]Checking if bypass worked...")
    console.log("\t[bold yellow]Sending action LOCKSCREEN.DISMISS")
    ssh_client.exec_command("activator send libactivator.lockscreen.dismiss")
    console.log(f"\t[bold yellow]Sending action START {properties.get('CFBundleIdentifier')}")
    ssh_client.exec_command(f"activator send {properties.get('CFBundleIdentifier')}")

def cleanup(args: argparse.ArgumentParser, sftp_client: paramiko.SFTPClient, properties: dict, decrypt_success: bool, console: Console):
    with console.status("Cleaning up...", spinner="grenade"):
        console.log("\t[bold yellow] Sending action SYSTEM.HOMEBUTTON")

        time.sleep(3)

        console.log(f"\tUninstalling {properties.get('CFBundleIdentifier')}...")

        subprocess.run(
            f'./libimobiledevice/ideviceinstaller.exe remove {properties.get("CFBundleIdentifier")}' if os.name == 'nt' else f'ideviceinstaller remove {properties.get("CFBundleIdentifier")}',
            stdout = subprocess.PIPE,
            text=True,
            check=True
        )

        console.log("Uninstalled!")

        for dumped_app in sftp_client.listdir('/private/var/mobile/Documents/Dumped/'):
            console.log(f"Copying {dumped_app} to {args.output_path}")

            final_out_path = os.path.join(args.output_path, str(random.randint(111111,999999)) + dumped_app)

            sftp_client.get(f"/private/var/mobile/Documents/Dumped/{dumped_app}", f"{final_out_path}")
            sftp_client.remove(f"/private/var/mobile/Documents/Dumped/{dumped_app}")
        console.log("Cleanup finished")

        if decrypt_success:
            return final_out_path
        else:
            return None
    

def decrypt(args: argparse.Namespace, config: configparser.ConfigParser, console: Console) -> None:
    ssh_client = connect_ssh(config, console)
    sftp_client = ssh_client.open_sftp()

    for path, _, files in os.walk(args.input_path):
        for file in files:
            try:
                extracted_ipa = utils.common.extract_ipa(os.path.join(path, file), console)
                properties = utils.common.get_app_properties(extracted_ipa, True, console)

                install_ipa(os.path.join(path, file), ssh_client, properties, console)

                _, clutch_output, _ = ssh_client.exec_command('clutch -i')
                clutch_output = clutch_output.read().decode('utf-8')
                console.log(clutch_output)

                package_number = get_package_number(clutch_output, properties)
                console.log(f"Target package number: {package_number}")

                decryption_successful = decrypt_app(args, config, properties, ssh_client, package_number, console)

                dumped_ipa = cleanup(args, sftp_client, properties, decryption_successful, console)
                
                if decryption_successful and args.delete:
                    os.remove(os.path.join(path, file))
                if args.sort:
                    utils.sort.sort_and_label(args, dumped_ipa, args.output_path, console)
            except Exception as e:
                console.log(f"[red bold] Error occured while decrypting: {e}")
                if args.debug: console.print_exception(show_locals=True)
    console.log("All done!")