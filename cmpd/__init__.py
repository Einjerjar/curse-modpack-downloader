import json
import os
import requests
import zipfile

from argparse import Namespace

from cmpd.ModStore import ModStore, AddonInfo, AddonFile
from cmpd.logger import logger


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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.88 Safari/537.36',
            'DNT': '1',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8,fil;q=0.7',
        }
        self.project_id = project_id
        self.store_dir = store_dir or 'cmpd_store'
        self.out_dir = out_dir or 'modpack'
        self.api = Namespace(**_api)
        self.info = None

        self.store = ModStore(self.store_dir)
        self.manifest = None

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

        # Print info
        self.print_pack_info(self.info)

        # Random sanity check
        if len(self.info.latest_files) == 0:
            logger.warning('Mod has no files ?')
            return

        # Save modpack info to store
        self.store.create_addon_details(self.info)

        # TODO   : Sanity check on whether this could also potentially download server files instead of client (BAD)
        # UPDATE : It seems like it might (which is bad, really bad, for me anyways, lol)
        #        :  will have to add a selection screen of sorts, hopefully can make it bearable
        #        :  and not annoying at all, lol
        # Download latest modpack file

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

        logger.info('-- Downloading modpack file')

        mod_file = self.store.download_to_store(self.info.latest_files[_newest])
        if not mod_file:
            logger.warning('!! Modpack download failed')
            return

        logger.info('-- Loading Manifest')

        # TODO : Handle Exceptions
        #      : possibly fileExceptions from zipfile and jsonExceptions from json
        pack_archive = zipfile.ZipFile(mod_file, 'r')
        manifest_data = json.loads(pack_archive.read('manifest.json').decode('utf-8'))
        pack_files = manifest_data['files']

        logger.info('-- Manifest Loaded')

        # TODO : Handle Exceptions and Edge Cases
        #   ps : no idea wtf the edge case I was talking about then, lol
        _p_len = len(pack_files)
        for i in range(_p_len):
            item = pack_files[i]
            p_id = item['projectID']
            f_id = item['fileID']

            logger.info('-- Downloading Mod [{} of {}] :: ID [{}]'.format(i+1, _p_len, f_id))
            info: AddonFile = self.get_addon_file_info(p_id, f_id)

            self.store.download_to_store(info)

        logger.info('-- Finished ?')

    def get_addon_info(self, addon_id):
        api = self.api

        f_store = self.store.get_addon_info(addon_id)
        if f_store:
            return f_store

        j_source = requests.get(api.addon_info.format(addon_id), headers=self.headers).content.decode('utf-8')
        j_data = json.loads(j_source)

        return AddonInfo.create_from_json(j_data)

    def get_addon_file_info(self, addon_id, file_id):
        api = self.api

        f_store = self.store.get_file_info(file_id)
        if f_store:
            return f_store

        j_source = requests.get(api.file_info.format(addon_id, file_id), headers=self.headers).content.decode(
            'utf-8')
        j_data = json.loads(j_source)

        return AddonFile.create_from_json(j_data)

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
