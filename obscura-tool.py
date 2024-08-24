import sys
import argparse
import configparser
import utils.decrypt
import utils.sort
from rich.console import Console

VERSION = '2024.8.2'

console = Console(log_path=False)
config = configparser.ConfigParser()
config.read('config.cfg')

argparse = argparse.ArgumentParser(description='Obscura Tool')
argparse.add_argument('--version', action="store_true", help='show version')
argparse.add_argument('--debug', action='store_true', help='print detailed exceptions')
subparser = argparse.add_subparsers(help='commands', dest='command')

parser_decrypt = subparser.add_parser("decrypt", help='decrypt encrypted iPA using automated iOS 6 bypass method')
parser_decrypt.add_argument('-i','--input-path', help="Directory to search for encrypted iPA files", required=True)
parser_decrypt.add_argument('-o','--output-path', help="Directory to output decrypted iPA files", required=True)
parser_decrypt.add_argument('-s', '--sort', action="store_true", default=True, help='Sort, label and organize decrypted iPA files using the Obscura format')
parser_decrypt.add_argument('-d', '--delete', action="store_true", default=True, help='Delete encrypted iPA files after decrypting')
parser_decrypt.add_argument('--attempts', type=int, default=10, help='Number of attempts to perform the iOS 6 bypass trick')
parser_decrypt.add_argument('--no-bypass', action='store_true', help='Attempt to decrypt without performing the iOS 6 bypas. Use this for decrypting iPAs tied to your devices AppleID.')

parser_sort = subparser.add_parser("sort", help='Sort, label and organize iPA files using the Obscura format')
parser_sort.add_argument('-i','--input-path', help="Directory to search for iPA files", required=True)
parser_sort.add_argument('-o','--output-path', help="Directory to output sorted iPA files", required=True)
parser_sort.add_argument('-d', '--delete', action="store_true", help="Delete original iPA files after sorting")

args = argparse.parse_args()

if args.version:
    print(f'Obscura Tool Version {VERSION}')
    print('Created by norep')
    print('https://github.com/norepnorep/obscura-tool')
    sys.exit(0)

if args.command == 'decrypt':
    utils.decrypt.decrypt(args, config, console)
elif args.command == 'sort':
    utils.sort.sort_and_label_batch(args, config, console)