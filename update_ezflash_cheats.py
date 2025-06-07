"""
This utility is intended to scrape and merge the libretro GBA cheat database
with the one provided by EZ-Flash for their Omega line of devices.  This will
give better English descriptions, and many times higher-quality cheats.

The command-line interface is self-documented.  Pass a `--help` flag to the
base script or after one of the subcommands for more information.  Try a
command like `python3 update_ezflash_cheats.py --help` or
`python3 update_ezflash_cheats.py patch --help` for more information.
"""

__version__ = "0.1.0"


import argparse
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import List
import xml.etree.ElementTree as ElementTree


GAME2ID_MAP_FILENAME = "GameID2cht.bin"
ENGLISH_CHEATS_DIRNAME = "Eng"
LIBRETRO_GBA_CHEATS_DIRNAME = "cht/Nintendo - Game Boy Advance"


@dataclass
class LibretroCheat:
    """
    Simple dataclass for strongly typed attribute names
    """
    desc: str
    code: str


class LibretroParseError(RuntimeError):
    """
    This error could indicate that either the input file is malformed, or
    that this script has an error in parsing.
    """
    pass


class LibretroCheatUnsupportedError(RuntimeError):
    """
    Indicates that the input file is valid, but the functionality encoded in
    a cheat entry is not supported by this script.  This is generally because
    the EZ-Flash Omega cheats are limited to fixing given addresses in memory
    to fixed values.  This limitation may not be accurate, but this seems to
    be all that's currently supported in the kernel.
    """
    pass


def parse_libretro_cheats_from_file(libretro_cheat_path: Path) -> List[LibretroCheat]:
    """
    Reads a libretro cheat file and encodes all cheats within as `LibretroCheat`
    objects.  This function is not responsible for parsing or converting the
    cheat codes themselves.
    """
    expected_num_cheats = None
    cheats_records = {}
    with open(libretro_cheat_path, "r") as libretro_cheat_file:
        for line in libretro_cheat_file:
            if len(line.strip()) == 0:
                continue

            key, val = line[:line.find("=")].strip(
            ), line[line.find("=") + 1:].strip()
            if key == "cheats":
                expected_num_cheats = int(val)
                continue
            elif key == "cheat_enable":
                # Malformed cheat file handling, should be cheatN_enable
                continue
            val = val[1:-1]

            key_name, key_type = key.split("_")
            if key_name not in cheats_records:
                cheats_records[key_name] = {}
            cheats_records[key_name][key_type] = val

    if len(cheats_records) != expected_num_cheats:
        raise LibretroParseError(
            f"Unexpected number of cheats in {libretro_cheat_path}.  "
            f"Got {len(cheats_records)}, expected {expected_num_cheats}"
        )

    return [
        LibretroCheat(cheats_records[key]["desc"], cheats_records[key]["code"])
        for key in sorted(cheats_records.keys())
    ]


def convert_libretro_cheat_to_ezflash(libretro_cheat: LibretroCheat) -> str:
    """
    Parses and converts Libretro Code Breaker cheat codes to EZ-Flash Omega
    format.
    @throws LibretroParseError if the input is malformed
    @throws LibretroCheatUnsupportedError if the input code is unsupported
    """
    result = f"[{libretro_cheat.desc}(LRDB)]\nON="

    toks = libretro_cheat.code.split("+")
    cheat_directives = []
    for i in range(0, len(toks), 2):
        # Catch malformed cheat codes
        try:
            addr_tok = toks[i]
            value_tok = toks[i + 1]
        except IndexError:
            raise LibretroParseError(
                "Unexpected number of tokens in Libretro cheat")

        if len(addr_tok) != 8:
            raise LibretroParseError(
                f"Expected cheat target address of len 8, got len {len(addr_tok)} for address {addr_tok}"
            )

        if not all(c in "0123456789ABCDEF" for c in value_tok):
            raise LibretroCheatUnsupportedError(
                f"Value is not hexadecimal ({value_tok})")

        # Switch based on the Code Breaker code type, as described here
        # https://www.sappharad.com/gba/codes/codebreaker-code-creation
        # See https://github.com/ez-flash/omega-de-kernel/blob/fb9d871d8df267cc9f322d41b7ee609552329c56/source/GBApatch.c#L473
        # for handling fo the leading "4" in the target address
        if addr_tok[0] == "3":
            cheat_directives.append(f"4{addr_tok[-4:]},{value_tok[-2:]}")
        elif addr_tok[0] == "8":
            cheat_directives.append(
                f"4{addr_tok[-4:]},{value_tok[2:]},{value_tok[:2]}")
        elif addr_tok[0] in ["4", "6", "7", "A", "D"]:
            raise LibretroCheatUnsupportedError(
                f"Code Breaker cheat type {addr_tok[0]} is not supported")
        else:
            raise LibretroParseError(
                f"Unknown Code Breaker cheat code type of '{addr_tok[0]}'")

    result += ";".join(cheat_directives)

    return result


def create_stub_ezflash_cht_file(destination: Path):
    """
    This may not be sufficient, but all this does for now is touch the destination
    file.  A parent directory is created if necessary beceause the EZ-Flash official
    database does not have a directory for roms with numeric ID >2800, but the
    libretro cheat database has cheats for roms with IDs in that range.
    """
    destination.parent.mkdir(exist_ok=True)
    destination.touch()


def patch_ezflash_cht_file(ezflash_cht_path: Path, libretro_cht_path: Path):
    """
    Patches the EZ-Flash cht file to prepend all compatible (and supported) libretro
    cheats.  Any cheat codes that are not parsed successfully or are not supported
    are skipped with a warning.
    """
    libretro_cheats = parse_libretro_cheats_from_file(libretro_cht_path)
    ezflash_cheats = []
    for libretro_cheat in libretro_cheats:
        try:
            ezflash_cheats.append(
                convert_libretro_cheat_to_ezflash(libretro_cheat))
        except (LibretroCheatUnsupportedError, LibretroParseError) as err:
            logging.warning(f"Skipping libretro cheat...{err}")

    with open(ezflash_cht_path, "rb") as cht_file:
        original_cht_file_contents = cht_file.read()

    with open(ezflash_cht_path, "wb") as cht_file_writable:
        cht_file_writable.write("\n\n".join(ezflash_cheats).encode("utf-8"))
        cht_file_writable.write(b"\n\n")
        cht_file_writable.write(original_cht_file_contents)

    print(
        f"Patched {str(ezflash_cht_path)} successfully, added {len(ezflash_cheats)} cheats")


def patch(ezflash_cheats_dir: Path, datfile_path: Path, libretro_database_dir: Path):
    """
    """
    game2id_map_path = ezflash_cheats_dir / GAME2ID_MAP_FILENAME

    # We need fast, repeated lookups into the DAT database, so parse into memory
    parsed_dat_tree = ElementTree.parse(datfile_path)
    serial_code_to_name = {}
    for rom in parsed_dat_tree.findall(".//rom"):
        try:
            rom_name = rom.attrib["name"]
            rom_serial_code = rom.attrib["serial"]
            serial_code_to_name[rom_serial_code] = rom_name[:rom_name.rfind(
                ".")][:rom_name.find("(")][:rom_name.find("&")].strip()
        except KeyError:
            # Assume this is BIOS entry
            logging.warning(
                f"Skipping ROM without `serial` field, this should be a BIOS file (name: {rom_name})")
            pass

    libretro_cheat_dir = libretro_database_dir / LIBRETRO_GBA_CHEATS_DIRNAME
    libretro_game_name_to_cheat_path = {}
    for path in libretro_cheat_dir.iterdir():
        game_name_prefix = path.name[:path.name.rfind(
            ".")][:path.name.find("(")][:path.name.find("_")].strip()
        libretro_game_name_to_cheat_path[game_name_prefix] = path

    with open(game2id_map_path, "r") as game2id_map_file:
        # Each DB entry is 8 characters long, first 4 chars is the serial code,
        # last 4 chars is the numeric ID.
        while game2id_entry := game2id_map_file.read(8):
            game_serial_code = game2id_entry[:4]
            game_numeric_id = int(game2id_entry[4:])

            try:
                game_name = serial_code_to_name[game_serial_code]
            except KeyError:
                logging.warning(
                    f"Could not find game with serial code {game_serial_code}")
                continue
            libretro_cheat_file_path = libretro_game_name_to_cheat_path.get(
                game_name)
            if libretro_cheat_file_path is None:
                logging.warning(
                    f"No libretro cheats for game name {game_name}, serial {game_serial_code}, numeric ID {str(game_numeric_id).zfill(4)}")
                continue

            cheat_file_numbered_subdir = Path(
                str(game_numeric_id - (game_numeric_id % 200)).zfill(4))
            target_cheat_file_path = (
                ezflash_cheats_dir / ENGLISH_CHEATS_DIRNAME /
                cheat_file_numbered_subdir /
                f"{str(game_numeric_id).zfill(4)}.cht"
            )

            if not target_cheat_file_path.exists():
                create_stub_ezflash_cht_file(target_cheat_file_path)

            patch_ezflash_cht_file(
                target_cheat_file_path, libretro_cheat_file_path)


def main_patch(args: argparse.Namespace):
    """
    `patch` subcommand entry point, intended for use only when called from CLI.
    Should this module ever be utilized as part of a larger project, this function
    should not be used by external code.
    """
    datfile_path = args.dat[0]
    ezflash_cheats_path = args.cheats_db[0]
    libretro_database_path = args.libretro_database[0]

    patch(ezflash_cheats_path, datfile_path, libretro_database_path)
    print("Patches applied")


def main():
    """
    CLI entry point, not intended to be used by external modules
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Can be specified multiple times in order to get more verbose output, like `-vvvv` for maximum verbosity",
    )
    parser.set_defaults(main=lambda *args: parser.print_help())
    subparsers = parser.add_subparsers(title="subcommands")

    patch_parser = subparsers.add_parser(
        "patch",
        help="Patch a local CHEATS directory with cheats obtained from the libretro-database repository",
    )
    patch_parser.add_argument(
        "-c",
        "--cheats-db",
        metavar="CHEATS",
        nargs=1,
        required=True,
        type=Path,
        help="Path to pre-downloaded unzipped CHEATS directory as downloaded from ezflash.cn.  THIS WILL BE MODIFIED.",
    )
    patch_parser.add_argument(
        "-d",
        "--dat",
        metavar="DATFILE",
        nargs=1,
        required="true",
        type=Path,
        help="Path to a .dat file (basic xml-formatted) obtained from Dat-O-Matic (No-Intro).",
    )
    patch_parser.add_argument(
        "-l",
        "--libretro-database",
        metavar="LIBRETRODATABASE",
        nargs=1,
        required=True,
        type=Path,
        help="Path to libretro-database repository root, previously cloned or downloaded."
    )
    patch_parser.set_defaults(main=main_patch)

    args = parser.parse_args()

    if args.verbose > 3:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose > 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose > 0:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.CRITICAL)

    args.main(args)


if __name__ == "__main__":
    main()
