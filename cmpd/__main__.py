import argparse

from cmpd import CMPD

parser = argparse.ArgumentParser(description='Tool for downloading modpacks from curseforge')
parser.add_argument('addon_id', type=str, help='the project id of the modpack')
parser.add_argument('-o', '--out', metavar='OUTPUT_FOLDER', default='modpack',
                    help='where to save the modpack output (minecraft folder)')
parser.add_argument('-s', '--store', metavar='APP_FOLDER', default='cmpd_store',
                    help='where to store local copies of the mod files')

args = parser.parse_args()

downloader = CMPD(args.addon_id, store_dir=args.store, out_dir=args.out)
downloader.download_modpack()
