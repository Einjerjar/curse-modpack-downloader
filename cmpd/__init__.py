import json
import os
import requests
import zipfile
import shutil

from argparse import Namespace
from pathlib import Path
from typing import List

from cmpd.ModStore import ModStore, AddonInfo, AddonFile
from cmpd.logger import logger
from distutils.dir_util import copy_tree, remove_tree


class CMPD:
    def __init__(self, project_id, store_dir=None, out_dir=None):
        # Data
        _api = {
            'root': 'https://addons-ecs.forgesvc.net/api/v2/',
            'addon_info': 'https://addons-ecs.forgesvc.net/api/v2/addon/{0}',
            'addon_desc': 'https://addons-ecs.forgesvc.net/api/v2/addon/{0}/description',
            'addon_files': 'https://addons-ecs.forgesvc.net/api/v2/addon/{0}/files',
            'file_info': 'https://addons-ecs.forgesvc.net/api/v2/addon/{0}/file/{1}',
            'file_link': 'https://addons-ecs.forgesvc.net/api/v2/addon/{0}/file/{1}/download-url',
        }

        # Self vars
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.88 Safari/537.36',
            'dnt': '1',
            'accept': '*/*',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,ja;q=0.8,fil;q=0.7',
        }
        self.project_id = project_id
        self.store_dir = store_dir or 'cmpd_store'
        self.out_dir = out_dir or 'modpack'
        self.api = Namespace(**_api)
        self.info = None

        self.store = ModStore(self.store_dir)
        self.manifest = None

        self.mod_files: List[AddonFile] = []

    def set_header_val(self, ref, val=None):
        if ref in self.headers and val is None:
            self.headers.pop(ref)
            return
        self.headers[ref] = val

    def unset_header_val(self, ref):
        if ref in self.headers:
            self.headers.pop(ref)

    def download_modpack(self):
        """
        Begins the downloading of the assigned modpack
        :return:
        """

        # Makes things easier
        o_dir = self.out_dir
        p = os.path

        # TODO : Handle exceptions
        # Make sure the output dir exists
        if not (p.exists(o_dir) and p.isdir(o_dir)):
            os.mkdir(o_dir)

        # Get modpack info
        self.info = self.get_addon_info(self.project_id)

        if self.info is None:
            logger.critical(' ❌ Halting process as the main modpack file cannot be retrieved')
            exit(-1)

        # Print info
        self.print_pack_info(self.info)

        # Random sanity check
        if len(self.info.latest_files) == 0:
            logger.warning('Mod has no files ?')
            return

        # Save modpack info to store
        self.store.create_addon_details(self.info)

        # FIXME  : Fix this naive implementation
        # Get which one is the newest (BETTER SOLUTION PLS LOL)
        #     ps : create a max/sort func?
        _newest = 0
        for i in range(len(self.info.latest_files)):
            if i == 0:
                continue
            f = self.info.latest_files[i]
            if f.timestamp > self.info.latest_files[_newest].timestamp:
                _newest = i

        logger.info('-- Downloading modpack file.')

        # TODO   : Sanity check on whether this could also potentially download server files instead of client (BAD)
        # UPDATE : It seems like it might (which is bad, really bad, for me anyways, lol)
        #        :  will have to add a selection screen of sorts, hopefully can make it bearable
        #        :  and not annoying at all, lol
        # Download latest modpack file
        mod_file = self.store.download_to_store(self.info.latest_files[_newest])
        if not mod_file:
            logger.warning(' ❌ Modpack download failed.')
            return

        logger.info('-- Loading Manifest.')

        # TODO : Handle Exceptions
        #      : possibly fileExceptions from zipfile and jsonExceptions from json
        pack_archive = zipfile.ZipFile(mod_file, 'r')
        manifest_data = json.loads(pack_archive.read('manifest.json').decode('utf-8'))
        pack_files = manifest_data['files']

        logger.info('-- Manifest Loaded.')

        # TODO : Handle Exceptions and Edge Cases
        #   ps : no idea wtf the edge case I was talking about then, lol
        _p_len = len(pack_files)
        for i in range(_p_len):
            item = pack_files[i]
            p_id = item['projectID']
            f_id = item['fileID']

            logger.info('-- #{} of {} :: ID [{}]'.format(str(i + 1).rjust(3), str(_p_len).rjust(3), f_id))
            info: AddonFile = self.get_addon_file_info(p_id, f_id)

            if info is None:
                logger.warning(' ! Skipping [{}] as it seems unavailable')
                continue

            info.set_linked_file(self.store.download_to_store(info))

            self.mod_files.append(info)

        # TODO : Ask to delete files not related to mod
        logger.info('-- Copying files to output folder [{}].'.format(self.out_dir))
        self.copy_mod_files()
        logger.info(' ✔ Done copying mod files to output folder.')

        logger.info('-- Copying mod overrides to output folder.')
        self.extract_overrides(pack_archive)
        logger.info(' ✔ Done copying overrides.')

        logger.info('-- Finished ?')

    def copy_mod_files(self):
        p = os.path
        # Make sure we're good with the dirs
        Path(p.join(self.out_dir, 'mods')).mkdir(parents=True, exist_ok=True)

        # TODO : Handle Exceptions
        for i in self.mod_files:
            if not i:
                continue
            src = i.linked_file_loc

            if src is None:
                logger.error(' ❌ Cannot find file linked to mod! skipping!')
                continue

            target = p.join(self.out_dir, 'mods', p.split(src)[1])

            # Random sanity (?) check (? lol)
            if not (p.exists(target) and p.isfile(target) and p.getsize(target) == p.getsize(src)):
                logger.info(' * Copying [{}] to out dir.'.format(i.get_linked_file()))
                shutil.copyfile(i.linked_file_loc, target)
                logger.info(' ✔ Copied  [{}] to out dir.'.format(i.get_linked_file()))
            else:
                logger.info(' ✔ File [{}] already exists in target folder and matches.'.format(i.get_linked_file()))

    def extract_overrides(self, pack_archive: zipfile.ZipFile):
        p = os.path

        # TODO : Slight chance of 'override' folder being a flexibly named dir
        #      :  that is hard referenced within the addon info json from the api
        for i in pack_archive.namelist():
            if i.startswith('overrides'):
                pack_archive.extract(i, self.out_dir)

        o_folder = p.join(self.out_dir, 'overrides')
        # o_temp = p.join(self.out_dir, '_overrides_temp')

        # TODO : Might be bad idea if overrides folder contains a folder named overrides (:3)
        copy_tree(o_folder, self.out_dir)
        remove_tree(o_folder)

    def get_addon_info(self, addon_id):
        api = self.api

        f_store = self.store.get_addon_info(addon_id)
        if f_store:
            return f_store

        try:
            j_source = requests.get(api.addon_info.format(addon_id), headers=self.headers).content.decode('utf-8')
            j_data = json.loads(j_source)

            return AddonInfo.create_from_json(j_data)
        except Exception as e:
            logger.h_except(e)
            logger.error(' ❌ Failed getting addon info for [{}]'.format(addon_id))

        return None

    def get_addon_file_info(self, addon_id, file_id):
        api = self.api

        f_store = self.store.get_file_info(file_id)
        if f_store:
            return f_store

        try:
            j_source = requests.get(api.file_info.format(addon_id, file_id), headers=self.headers).content.decode(
                'utf-8')
            j_data = json.loads(j_source)

            return AddonFile.create_from_json(j_data)
        except Exception as e:
            logger.h_except(e)
            logger.error(' ❌ Failed getting file info for [{}]'.format(file_id))

        return None

    @staticmethod
    def print_pack_info(pack_info: AddonInfo):
        logger.info('''
        -----------------------------------
        :: {}
        -----------------------------------
         : {}
        -----------------------------------
        :: Project ID:    {}
        -----------------------------------'''.format(
            pack_info.d_name,
            pack_info.summary,
            pack_info.uid,
        ))