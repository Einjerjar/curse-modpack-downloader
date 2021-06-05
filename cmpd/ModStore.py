import humanize
import json
import os
import requests as req

from pathlib import Path

from cmpd.Addons import AddonInfo, AddonFile
from cmpd.logger import logger


# ------------------------------------
# Mod Store structure
# ------------------------------------
# store
#   - data
#     - addons
#         - {addon_id}.json
#     - files
#         - {file_id}.json
#   - files
#     - {file_id}
#         - {file_name}
# ------------------------------------

class ModStore:
    def __init__(self, store_dir, headers=None, chunk_size: int = None):
        p = os.path

        # TODO : Handle Exceptions
        # Make sure the dir exists
        if not (p.exists(store_dir) and p.isdir(store_dir)):
            Path(store_dir).mkdir(parents=True, exist_ok=True)

        self.store_dir = store_dir
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.88 Safari/537.36',
            'DNT': '1',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8,fil;q=0.7',
        }

        # 1024 B * 512 = 512 KB
        self.chunk_size = chunk_size or (1024 * 512)

    def prep_folder(self, folder: str):
        """
        Prepares a folder for the app
        :param folder: the folder to create
        """
        if folder is None or len(folder.strip()) == 0:
            logger.warning('Need valid folder target')
            return

        s = self.store_dir
        p = os.path

        target_folder = p.join(s, folder)

        if not (p.exists(target_folder) and p.isdir(target_folder)):
            Path(target_folder).mkdir(parents=True, exist_ok=True)

    def prep_data_folder(self):
        """
        Prepares the data folder
        """
        self.prep_folder('data/addons')
        self.prep_folder('data/files')

    def prep_file_folder(self):
        """
        Prepares the file folder
        """
        self.prep_folder('files')

    def create_addon_details(self, addon_info: AddonInfo):
        """
        Generates a json file with the addon's info
        :param addon_info: the info to use
        """
        self.prep_data_folder()
        detail_file = os.path.join(self.store_dir, 'data', 'addons', '{}.json'.format(addon_info.uid))

        with open(detail_file, 'w') as f:
            json.dump(addon_info.get_json(), f)

    def create_file_details(self, addon_file: AddonFile):
        """
        Generates a json file with the addon file's info
        :param addon_file: the info to use
        """
        self.prep_data_folder()
        detail_file = os.path.join(self.store_dir, 'data', 'files', '{}.json'.format(addon_file.uid))

        with open(detail_file, 'w') as f:
            json.dump(addon_file.get_json(), f)

    def download_to_store(self, addon_file: AddonFile):
        """
        Downloads an addon file to the store and registers it
        :param addon_file: info of the file to download
        """

        # Save the current target's details to store
        self.create_file_details(addon_file)

        # Downloader vars
        _max_retries = 3
        _retries = 0
        _success = False

        p = os.path

        # Just making sure (srsly)
        self.prep_file_folder()

        target = p.join(self.store_dir, 'files', str(addon_file.uid), addon_file.file_name)

        # Check if file already exists and matches file length,
        #  else, make sure that all the preceding dirs are made
        if p.exists(target) and p.isfile(target):
            if p.getsize(target) == addon_file.length:
                logger.info(' / File [{}] already exists seems valid.'
                            .format(addon_file.d_name))
                return target
            else:
                logger.warn(' X File [{}] exists but seems corrupted, redownloading.'
                            .format(addon_file.d_name))
        else:
            Path(p.split(target)[0]).mkdir(parents=True, exist_ok=True)

        while _retries < _max_retries:
            try:
                _r = req.get(addon_file.url, stream=True)
                _size = _r.headers.get('content-length')

                if _size is None:
                    logger.error('XX Headers for downloading [] does not have content-length ?')
                    logger.error(_r.content)
                    _retries += 1
                    continue

                with open(target, 'wb') as f:
                    logger.info('   Attempt #{} :: Downloading {} :: [{}]'.format(
                        _retries,
                        humanize.naturalsize(addon_file.length).rjust(8),
                        addon_file.d_name)
                    )

                    f_load = 0
                    f_size = int(_size)
                    for data in _r.iter_content(chunk_size=self.chunk_size):
                        f_load += len(data)
                        f.write(data)
                        logger.info('   {}% :: {} of {}'.format(
                            str(int((f_load / f_size) * 100)).rjust(9),
                            humanize.naturalsize(f_load).rjust(8),
                            humanize.naturalsize(f_size).rjust(8)
                        ))

                _success = True
                break
            except Exception as e:
                _retries += 1
                logger.h_except(e)
                logger.error(' X Failed, Retrying [{}].'.format(_retries))

        if not _success:
            logger.error(' X Failed to download [x] after trying [y] times, skipping.')
            return None

        logger.info(' / Downloaded [{}].'.format(addon_file.d_name))
        return target

    def get_addon_info(self, addon_id: int):
        """
        Checks if info about an addon is available
        :param addon_id: the id of the addon
        :return: the addon info
        """
        p = os.path
        addon_data = p.join(self.store_dir, 'data', 'addons', '{}.json'.format(addon_id))

        # Check if it exists first
        if not (p.exists(addon_data) and p.isfile(addon_data)):
            return False

        # TODO : Handle Exceptions
        a_data = open(addon_data, 'r').read()
        if len(a_data) == 0:
            logger.critical('XX [addon_data] for [{}] is empty!! returning a false!'.format(addon_id))
            return False
        return AddonInfo.create_from_store(json.loads(a_data), self)

    def get_file_info(self, file_id):
        """
        Checks if a file is available on the store
        :param file_id: the file id to test for
        :return:
        """
        p = os.path
        file_data = p.join(self.store_dir, 'data', 'files', '{}.json'.format(file_id))

        # Check if it exists first
        if not (p.exists(file_data) and p.isfile(file_data)):
            return False

        # TODO : Handle Exceptions
        a_data = open(file_data, 'r').read()
        if len(a_data) == 0:
            logger.critical('XX [file_data] for [{}] is empty!! returning a false!'.format(file_id))
            return False
        return AddonFile.create_from_store(json.loads(a_data))

    def get_file_with_id(self, file_id):
        """
        Gets the local file location of a target id
        :param file_id: the file id to locate
        :return:
        """
        pass
