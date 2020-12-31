# curse-modpack-downloader

An automated curseforge/twitch modpack downloader for minecraft (? and possibly other curseforge supported games)

Api loosely based off [ https://github.com/Gaz492/TwitchAPI ]

## Usage
### As Module
```shell script
python -m cmpd <project_id> [-o, --output modpack_folder] [-s, --store store_folder]
```

### As package
Import the package and create an instance with the
project's addon/project id (from curseforge/twitch)
then finally run the download_modpack function like so
```python
import cmpd

project_id = 123456     # str or int
downloader = cmpd.CMPD(project_id)
downloader.download_modpack()
```

You can also set the mod storage directory and modpack
output directory like so (defaults to `cmpd_store` and `modpack` respectively)
```python
cmpd.CMPD(project_id, store_dir='store_dir', out_dir='modpack_dir')
```

### Process
When ran, the app creates a basic mod storage on the target mod
storage directory (defaults to `cmpd_store`) and stores
basic infos that runs through it (addon and file info).

The app will then download all the necessary files, storing
local copies of the mod files so that it can reuse said files
for any future downloads.

Finally, the app will copy all the required files from the mod
store to the target directory (defaults to `modpack`) then extracts
the overrides from the modpack's base archive

## TODO
* [x] ~~Allow running as python module~~
* [ ] Allow direct downloading of modpack to target dir (ignore/skip mod storage)
* [ ] Ask to delete files not related to current mod :3
* [ ] Documentations, lol
* [ ] GUI OwO
* [x] ~~Allow a more obvious and safe indirect modification of default request headers ?~~

### Send support :3
<a href='https://ko-fi.com/X8X831J1L' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://cdn.ko-fi.com/cdn/kofi1.png?v=2' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>