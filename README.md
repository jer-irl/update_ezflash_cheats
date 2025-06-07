# update_ezflash_cheats

Please see self-contained documentation in the header of `update_ezflash_cheats.py` for the most up-to-date usage information.

## Overview

This utility is intended to scrape and merge the libretro GBA cheat database with the one provided by EZ-Flash for their Omega line of devices.  This will give better English descriptions, and many times higher-quality cheats.

The command-line interface is self-documented.  Pass a `--help` flag to the base script or after one of the subcommands for more information.  Try a command like `python3 update_ezflash_cheats.py --help` or `python3 update_ezflash_cheats.py patch --help` for more information.

## Example usage

Not necessarily up to date:

```bash
% python3 update_ezflash_cheats.py patch --help
usage: update_ezflash_cheats.py patch [-h] -c CHEATS -d DATFILE -l LIBRETRODATABASE

options:
  -h, --help            show this help message and exit
  -c, --cheats-db CHEATS
                        Path to pre-downloaded unzipped CHEATS directory as downloaded from ezflash.cn. THIS WILL BE MODIFIED.
  -d, --dat DATFILE     Path to a .dat file (basic xml-formatted) obtained from Dat-O-Matic (No-Intro).
  -l, --libretro-database LIBRETRODATABASE
                        Path to libretro-database repository root, previously cloned or downloaded.

% python3 update_ezflash_cheats.py patch --cheats-db /path/to/downlaoded/CHEAT --dat /path/to/Nintendo\ -\ Game\ Boy\ Advance\ \(20250602-123637\).dat --libretro-database /path/to/libretro-database-master
...
Patched /path/to/downlaoded/CHEAT/Eng/0000/0037.cht successfully, added 7 cheats
Patched /path/to/downlaoded/CHEAT/Eng/0000/0038.cht successfully, added 7 cheats
Patched /path/to/downlaoded/CHEAT/Eng/0000/0039.cht successfully, added 2 cheats
Patched /path/to/downlaoded/CHEAT/Eng/0000/0040.cht successfully, added 4 cheats
...
Patches applied
```

## Status

Currently tested with libretro-database v1.8.2, and requires a recent Python 3. I have only tested the script with Python 3.8.5 on Ubuntu.  Other than Python and the input files, there should be no other dependencies.

The flakiest part of this utility is the correlation between ROM names as listed in DAT files, and the corresponding libretro-database *.cht file.  I've tried tracing how RetroArch does this in its *.rdb database, but I haven't yet found that functionality in the code.

## Other discussions

- [Mentioned in reddit Thread](https://www.reddit.com/r/flashcarts/comments/110nb7k/how_do_i_use_cheats_on_ezflash_omega/)
- [gbatemp thread](https://gbatemp.net/threads/convert-the-libretro-database-cheats-to-ezflash.652742/)

## References

- [EZ-Flash Omega Definitive Edition kernel source](https://github.com/ez-flash/omega-de-kernel)
- [Previous similar effort by largemoose421](https://gbatemp.net/threads/simple-action-replay-to-ez-flash-omega-cht-converter.559163/#post-8964955)
- [Overview on hardware-based game cheats](https://macrox.gshi.org/The%20Hacking%20Text.htm)
- [Documentation of Code Breaker cheat format](https://www.sappharad.com/gba/codes/codebreaker-code-creation)
- [RetroArch cheat documentation (not too useful)](https://github.com/libretro/docs/blob/master/docs/guides/cheat-codes.md)
- [EZ-Flash Omega cheat tutorial/guide](https://www.reddit.com/r/Gameboy/comments/hcq2g6/ezflash_omega_cheat_system_tutorial/)

## Resources

- [EZ-Flash Omega cheat library download link (zipped)](https://www.ezflash.cn/zip/omegacheatlibrary.zip)
- [libretro-database master branch download link (zipped)](https://github.com/libretro/libretro-database/archive/refs/heads/master.zip)
- [DAT file download page](https://datomatic.no-intro.org/index.php?page=download&op=dat&s=23)

