from cmpd import CMPD
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('pack_id', type=int, help='Project ID of the modpack')

args = parser.parse_args()

pack_id = args.pack_id
downloader = CMPD(pack_id)
downloader.download_modpack()
