# Synchronic - Sync between Plex and MyAnimeList

This is a fairly simple script that will scan your Anime section on Plex and attempt to map it to the corresponding MyAnimeList anime item. If found, this will set the status and number of episodes watched for the show using the data found in Plex.

##### WARNING:
This will overwrite any existing entries for each item it finds, so use with care (yes, that means potential data loss)! I also don't guarantee any successful mappings, so expect some errors or incorrect matches to pop up (feel free to submit PRs to fix as needed). Use at your own discretion! If you want to see the output before it actually saves, comment out the line where `self.update(item, item_id)` is called.

#### Setup (Linux, macOS)
```
$ git clone git@github.com:xharv14/synchronic.git ~/synchronic
$ cd ~/synchronic
$ pip install -r requirements.txt
$ chmod +x synchronic.py
# cp config.example.yml config.yml
$ $EDITOR config.yml  # (modify as needed)
$ ./synchronic.py  # (you may need to fix the shebang, or run directly)
```

It should be a similar setup for Windows, though I haven't tested it.
