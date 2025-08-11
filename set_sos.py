import argparse
import concurrent.futures
import json
import time

import miwi


def set_sos(imei: str, settings: dict):
    timestamp = int(time.time() * 1000)

    payload = {
        "Imei": imei,
        "Time": timestamp,
        "CommandCode": "0001",
        "CommandValue": settings
    }

    return miwi.send_command(payload)


def process_imei(imei, settings):
    results = []

    try:
        result = "OK" if set_sos(imei, settings) else "Failed"
        results.append(f"[SOS] set {imei}: {result}")
    except Exception as e:
        results.append(f"set {imei}: Exception {str(e)}")

    return results


def main(imeis: list, opt: argparse.Namespace):
    settings = miwi.read_settings(opt.setting, "txt")

    # split into chunk per 10
    chunks = [imeis[i:i + 10] for i in range(0, len(imeis), 10)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for chunk in chunks:
            futures = {executor.submit(process_imei, imei, settings): imei for imei in chunk}

            for future in concurrent.futures.as_completed(futures):
                results = future.result()
                for result in results:
                    print(result)
            
            time.sleep(0.2)

def main_set_sos(imeis: list, filename: str):
    settings = miwi.read_settings_by_file(filename, "txt")

    # split into chunk per 10
    chunks = [imeis[i:i + 10] for i in range(0, len(imeis), 10)]
    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for chunk in chunks:
            futures = {executor.submit(process_imei, imei, settings): imei for imei in chunk}

            for future in concurrent.futures.as_completed(futures):
                results = future.result()
                for result in results:
                    print(result)
            
            time.sleep(0.2)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="watches.txt", help="Watch Imei files")
    parser.add_argument("--imei", type=str, help="Imei Number")
    parser.add_argument("--setting", type=str, required=True, default="setting.txt", help="Config settings")
    opt = parser.parse_args()

    imeis = miwi.read_imeis(opt)
    if imeis:
        main(imeis, opt)
    else:
        raise FileNotFoundError(f"No Imeis found")
