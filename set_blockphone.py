import argparse
import concurrent.futures
import time

import miwi


def set_blockphone(imei: str, value="1"):
    timestamp = int(time.time() * 1000)

    payload = {"Imei": imei, "Time": timestamp, "CommandCode": "9601", "CommandValue": value}
    return miwi.send_command(payload)


def process_imei(imei, value):
    results = []

    try:
        result = "OK" if set_blockphone(imei, value) else "Failed"
        results.append(f"[BlockPhone] set {imei} - value: {value}: {result}")
    except Exception as e:
        results.append(f"set {imei}: Exception {str(e)}")

    return results


def main(imeis: list, opt: argparse.Namespace):
    # split into chunk per 10
    chunks = [imeis[i : i + 10] for i in range(0, len(imeis), 10)]

    value = "1" if opt.task == "on" else "0"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for chunk in chunks:
            # Process each chunk in parallel
            futures = {executor.submit(process_imei, imei, value): imei for imei in chunk}

            for future in concurrent.futures.as_completed(futures):
                for result in future.result():
                    print(result)

            time.sleep(0.2)  # Wait between chunks

def main_set_block_phone(imeis: list, flag: bool):
    # split into chunk per 10
    chunks = [imeis[i : i + 10] for i in range(0, len(imeis), 10)]

    results = []
    value = "1" if flag else "0"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for chunk in chunks:
            # Process each chunk in parallel
            futures = {executor.submit(process_imei, imei, value): imei for imei in chunk}

            for future in concurrent.futures.as_completed(futures):
                for result in future.result():
                    results.append(result)

            time.sleep(0.2)  # Wait between chunks
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="watches.txt", help="Watch Imei files")
    parser.add_argument("--imei", type=str, help="Imei Number")
    parser.add_argument("--task", type=str, required=True, choices=["on", "off"], help="Task: on/off")
    opt = parser.parse_args()

    imeis = miwi.read_imeis(opt)
    if imeis:
        main(imeis, opt)
    else:
        raise FileNotFoundError(f"No Imeis found")
