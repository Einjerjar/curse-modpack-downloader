import argparse

from cmpd import CMPD


parser = argparse.ArgumentParser(description='Tool for downloading modpacks from curseforge')
parser.add_argument('addon_id', type=str, help='the project id of the modpack')

args = parser.parse_args()

downloader = CMPD(args.addon_id)
downloader.download_modpack()
