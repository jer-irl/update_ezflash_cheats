import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


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


def convert_file(in_file_path: Path, out_dir_path: Path):
    cheats_records = {}
    with open(in_file_path, "r") as libretro_cheat_file:
        for line in libretro_cheat_file:
            if len(line.strip()) == 0:
                continue

            key, val = line[:line.find("=")].strip(), line[line.find("=") + 1:].strip()
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
            f"Unexpected number of cheats in {in_file_path}.  "
            f"Got {len(cheats_records)}, expected {expected_num_cheats}"
        )

    cheats = [
        LibretroCheat(cheats_records[key]["desc"], cheats_records[key]["code"])
        for key in sorted(cheats_records.keys())
    ]



def convert(in_tsv: Path, out_dir:Path):
    out_dir.mkdir(exist_ok=True)

    with open(in_tsv, "r") as in_file:
        lines = in_file.readlines()
        lines = lines[2:]
        for entry in csv.DictReader(lines, dialect="excel-tab"):
            game = entry["Game"]
            game_dir = out_dir / game
            game_dir.mkdir(exist_ok=True)
            cheat_path = game_dir / (entry["Effect…"].strip().replace(" ", "_").replace("/", "_") + ".txt")
            cheats = [code.strip() for code in entry["Key in…"].split("+")]
            with open(cheat_path, "w") as out_file:
                out_file.write("\n".join(cheats) + "\n")



    # for file in in_dir.iterdir():
    #     if file.is_dir():
    #         convert(file, out_dir / file.name)
    #     elif file.is_file() and file.suffix == ".cht" and "(Game Genie)" in file.name:
    #         convert_file(file, out_dir)
    #     else:
    #         raise RuntimeError("Unexpected file type")




def main_convert(args: argparse.Namespace):
    convert(args.in_tsv[0], args.out_dir[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in-tsv", action="store", nargs=1, required=True, type=Path)
    parser.add_argument("-o", "--out-dir", action="store", nargs=1, required=True, type=Path)
    parser.set_defaults(main=main_convert)

    args = parser.parse_args()
    args.main(args)


if __name__ == "__main__":
    main()
