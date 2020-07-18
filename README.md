# curse-modpack-downloader

An automated curseforge/twitch modpack downloader for minecraft (? and possibly other curseforge supported games)

Api loosely based off from [ https://github.com/Gaz492/TwitchAPI ] 

---

## Usage

Will soon work on a more modular approach but currently
works as follows (or just check `runner.py`)

import the package and create an instance with the
project's addon/project id (from curseforge/twitch)

then finally run the download_modpack function like so
```python
import cmpd

project_id = 123456
downloader = cmpd.CMPD(project_id)
downloader.download_modpack()
```

## TODO
* [ ] Ask to delete files not related to mod :3
* [ ] Documentations, lol
* [ ] GUI OwO
* [ ] Allow running as python module