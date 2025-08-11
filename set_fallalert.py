import argparse
import time

import miwi


def turn_on(imei: str, level=8):
    timestamp = int(time.time() * 1000)
    payload = {
        "Imei": imei,
        "Time": timestamp,
        "CommandCode": "9203",
        "CommandValue": "1,1"
    }

    if miwi.send_command(payload):
        timestamp = int(time.time() * 1000)
        payload = {
            "Imei": imei,
            "Time": timestamp,
            "CommandCode": "9722",
            "CommandValue": str(level)
        }
        return miwi.send_command(payload)



    return False


def turn_off(imei: str):
    timestamp = int(time.time() * 1000)
    payload = {
        "Imei": imei,
        "Time": timestamp,
        "CommandCode": "9203",
        "CommandValue": "0,0"
    }

    return miwi.send_command(payload)


def main(imeis: list, opt: argparse.Namespace):
    # split into chunk per 10
    chunks = [imeis[i:i + 10] for i in range(0, len(imeis), 10)]

    for chunk in chunks:
        for imei in chunk:
            try:
                if opt.task == "on":
                    result = "OK" if turn_on(imei, opt.level) else "Failed"
                    print(f"set fall alert(level={opt.level}) {imei}: {result}")
                elif opt.task == "off":
                    result = "OK" if turn_off(imei) else "Failed"
                    print(f"turn off fall alert {imei}: {result}")

            except Exception as e:
                print(f"{imei}: Exception {str(e)}")
                continue

        time.sleep(0.5)

def main_set_alert(imeis: list, switch: bool = True):
    # split into chunk per 10
    chunks = [imeis[i:i + 10] for i in range(0, len(imeis), 10)]
    message = []
    for chunk in chunks:
        for imei in chunk:
            try:
                if switch == True:
                    result = "OK" if turn_on(imei, 8) else "Failed"
                    message.append (f"set fall alert(level={8}) {imei}: {result}\n")
                elif switch == False:
                    result = "OK" if turn_off(imei) else "Failed"
                    message.append(f"turn off fall alert {imei}: {result}\n")

            except Exception as e:
                print(f"{imei}: Exception {str(e)}")
                continue

        time.sleep(0.5)
    return message

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default="watches.txt", help="Watch Imei files")
    parser.add_argument("--imei", type=str, help="Imei Number")
    parser.add_argument('--task', type=str, required=True, choices=['on', 'off'], help="Task: on/off")
    parser.add_argument("--level", type=int, default=8, help="Sensitivity level: 1-8")
    opt = parser.parse_args()

    imeis = miwi.read_imeis(opt)
    if imeis:
        main(imeis, opt)
    else:
        raise FileNotFoundError(f"No Imeis found")
