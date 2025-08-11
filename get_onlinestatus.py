import miwi
import argparse
from pathlib import Path


def main(imeis: list, opt: argparse.Namespace):
    online_imeis = miwi.get_devices()
    for imei in imeis:
        if imei in online_imeis:
            print(f"{imei} online")
        else:
            print(f"{imei} offline")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="watches.txt", help="Watch Imei files")
    parser.add_argument("--imei", type=str, help="Imei Number")
    opt = parser.parse_args()

    imeis = miwi.read_imeis(opt)
    if imeis:
        main(imeis, opt)
    else:
        raise FileNotFoundError(f"Not Imeis found")