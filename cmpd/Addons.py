from datetime import datetime

from typing import List

from cmpd import ModStore


class AddonFile:
    def __init__(self, uid: int, addon_uid: int, d_name: str, file_name: str, url: str,
                 length: int, fingerprint: int, timestamp: float):
        self.uid = uid
        self.addon_uid = addon_uid
        self.d_name = d_name
        self.file_name = file_name
        self.url = url
        self.length = length
        self.timestamp = timestamp

        # Just in case we wanna find the addon root
        self.fingerprint = fingerprint

    def get_json(self):
        return {
            'uid': self.uid,
            'addon_uid': self.addon_uid,
            'd_name': self.d_name,
            'file_name': self.file_name,
            'url': self.url,
            'length': self.length,
            'timestamp': self.timestamp,
            'fingerprint': self.fingerprint,
        }

    @staticmethod
    def create_from_json(addon_file, addon_uid=None, fingerprint=None):
        uid = addon_file['id']
        addon_uid = addon_file['projectId'] if 'projectId' in addon_file else (addon_uid or -1)
        d_name = addon_file['displayName']
        file_name = addon_file['fileName']
        url = addon_file['downloadUrl']
        length = addon_file['fileLength']
        fingerprint = addon_file['fingerprint'] if 'fingerprint' in addon_file else (fingerprint or -1)

        # TODO : Figure out a less hacky way of dealing with this, perhaps with another lib/package?
        # Converts timestamp to float, cracks up zulu format to allow python to read it
        #  discards milliseconds since it's a paint to add new stuff just for this one part
        #  lol
        timestamp = datetime.fromisoformat(
                addon_file['fileDate'].replace('Z', '').split('.')[0]
            ).timestamp()

        return AddonFile(uid, addon_uid, d_name, file_name, url, length, fingerprint, timestamp)

    @staticmethod
    def create_from_store(addon_file):
        uid = addon_file['uid']
        addon_uid = addon_file['addon_uid']
        d_name = addon_file['d_name']
        file_name = addon_file['file_name']
        url = addon_file['url']
        length = addon_file['length']
        timestamp = addon_file['timestamp']
        fingerprint = addon_file['fingerprint']

        return AddonFile(uid, addon_uid, d_name, file_name, url, length, fingerprint, timestamp)


class AddonInfo:
    def __init__(self, uid: int, d_name: str, summary: str, url: str, latest_files: List[AddonFile], categories=None):
        self.uid = uid
        self.d_name = d_name
        self.summary = summary
        self.url = url
        self.latest_files = latest_files
        self.categories = categories

    def get_json(self):
        latest_files = []

        for i in self.latest_files:
            latest_files.append(i.uid)

        return {
            'uid': self.uid,
            'd_name': self.d_name,
            'summary': self.summary,
            'url': self.url,
            'latest_files': latest_files,
            'categories': self.categories,
        }

    @staticmethod
    def create_from_json(addon_info):
        uid = addon_info['id']
        d_name = addon_info['name']
        summary = addon_info['summary']
        url = addon_info['websiteUrl']
        latest_files = addon_info['latestFiles']

        for i in range(len(latest_files)):
            latest_files[i] = AddonFile.create_from_json(latest_files[i])

        return AddonInfo(uid, d_name, summary, url, latest_files)

    @staticmethod
    def create_from_store(addon_info, store: ModStore = None):
        uid = addon_info['uid']
        d_name = addon_info['d_name']
        summary = addon_info['summary']
        url = addon_info['url']
        latest_files = addon_info['latest_files']

        if store:
            _n_temp = []
            for i in range(len(latest_files)):
                temp = store.get_file_info(latest_files[i])
                if temp:
                    _n_temp.append(temp)
            latest_files = _n_temp

        return AddonInfo(uid, d_name, summary, url, latest_files)
