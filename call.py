import argparse
import datetime
import time

import miwi


def send(imei: str):
    payload = {
        "Imei": imei,
        "CommandCode": "0315",
        "CommandValue": "85212345,yx_jh_2442,1"
    }

    return miwi.send_command(payload, timeout=10)


def main(imeis: list, opt: argparse.Namespace):
    # split into chunk per 10
    chunks = [imeis[i:i + 10] for i in range(0, len(imeis), 10)]

    for chunk in chunks:
        for imei in chunk:
            try:
                result = "OK" if send(imei) else "Failed"
                print(f"calling {imei}: {result}")
            except Exception as e:
                print(f"calling {imei}: Exception {str(e)}")
                continue

        time.sleep(0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="watches.txt", help="Watch Imei files")
    parser.add_argument("--imei", type=str, help="Imei Number")
    opt = parser.parse_args()

    imeis = miwi.read_imeis(opt)
    if imeis:
        main(imeis, opt)
    else:
        raise FileNotFoundError(f"No Imeis found")
