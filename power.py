import argparse
import time

import miwi


def send(imei: str, cmd: str):
    timestamp = int(time.time() * 1000)
    payload = {
        "Imei": imei,
        "Time": timestamp,
        "CommandCode": "0010" if cmd == "reboot" else "0048",
        "CommandValue": ""
    }

    return miwi.send_command(payload)


def main(imeis: list, opt: argparse.Namespace):
    # split into chunk per 10
    chunks = [imeis[i:i + 10] for i in range(0, len(imeis), 10)]
    cmd_name = "turn off" if opt.task == "off" else "reboot"

    for chunk in chunks:
        for imei in chunk:
            try:
                result = "OK" if send(imei, opt.task) else "Failed"
                print(f"{cmd_name} {imei}: {result}")
            except Exception as e:
                print(f"{cmd_name} {imei}: Exception {str(e)}")
                continue

        time.sleep(0.5)

def main_power(imeis: list, switch: bool):
    # split into chunk per 10
    chunks = [imeis[i:i + 10] for i in range(0, len(imeis), 10)]
    results = []

    for chunk in chunks:
        for imei in chunk:
            try:
                result = "OK" if send(imei, "on" if switch else "off") else "Failed"
                results.append(f"{imei}: {result}\n")
            except Exception as e:
                results.append(f"{imei}: Exception {str(e)}")

        time.sleep(0.5)

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="watches.txt", help="Watch Imei files")
    parser.add_argument("--imei", type=str, help="Imei Number")
    parser.add_argument('--task', type=str, required=True, choices=['reboot', 'off'], help="Task: reboot/off")
    opt = parser.parse_args()

    imeis = miwi.read_imeis(opt)
    if imeis:
        main(imeis, opt)
    else:
        raise FileNotFoundError(f"No Imeis found")
