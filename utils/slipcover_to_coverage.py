from coverage import CoverageData
import json
from pathlib import Path
import sys


def convert_slipcover_json_to_coverage(input_path, output_path):
    input_json = json.load(Path(input_path).open("r"))
    data_file = CoverageData(output_path)
    data_file.read()

    line_data = {
        str(Path().joinpath(file).resolve()): data["executed_lines"]
        for file, data in input_json["files"].items()
    }
    data_file.add_lines(line_data)
    data_file.write()


def main():
    infile = sys.argv[1]
    outfile = sys.argv[2]
    convert_slipcover_json_to_coverage(infile, outfile)


if __name__ == "__main__":
    main()