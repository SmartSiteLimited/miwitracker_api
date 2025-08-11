import argparse
import concurrent.futures
import time

import miwi


def set_heartrates(imei: str):
    timestamp = int(time.time() * 1000)

    payload = {
        "Imei": imei,
        "Time": timestamp,
        "CommandCode": "2815",
        "CommandValue": '[{"TimeInterval":"300","Switch":"1"}]'
    }

    return miwi.send_command(payload)


def set_bodytemp(imei: str):
    timestamp = int(time.time() * 1000)

    payload = {
        "Imei": imei,
        "Time": timestamp,
        "CommandCode": "9113",
        "CommandValue": '1,1'
    }

    return miwi.send_command(payload)

def set_gpstrack(imei: str):
    timestamp = int(time.time() * 1000)

    payload = {
        "Imei": imei,
        "Time": timestamp,
        "CommandCode": "0305",
        "CommandValue": '10'
    }

    return miwi.send_command(payload)



def process_imei(imei):
    results = []
    
    try:
        result = "OK" if set_heartrates(imei) else "Failed"
        results.append(f"[Heartrate] set {imei}: {result}")
    except Exception as e:
        results.append(f"set {imei}: Exception {str(e)}")
    
    try:
        result = "OK" if set_bodytemp(imei) else "Failed"
        results.append(f"[BodyTemp] set {imei}: {result}")
    except Exception as e:
        results.append(f"set {imei}: Exception {str(e)}")
    
    try:
        result = "OK" if set_gpstrack(imei) else "Failed"
        results.append(f"[GPS Track] set {imei}: {result}")
    except Exception as e:
        results.append(f"set {imei}: Exception {str(e)}")
    
    return results

def main(imeis: list, opt: argparse.Namespace):
    # split into chunk per 10
    chunks = [imeis[i:i+10] for i in range(0, len(imeis), 10)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for chunk in chunks:
            # Process each chunk in parallel
            futures = {executor.submit(process_imei, imei): imei for imei in chunk}
            
            for future in concurrent.futures.as_completed(futures):
                for result in future.result():
                    print(result)

            time.sleep(0.2)  # Wait between chunks

def main_set_health(imeis: list):
    # split into chunk per 10
    chunks = [imeis[i:i+10] for i in range(0, len(imeis), 10)]
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for chunk in chunks:
            # Process each chunk in parallel
            futures = {executor.submit(process_imei, imei): imei for imei in chunk}
            
            for future in concurrent.futures.as_completed(futures):
                for result in future.result():
                    results.append(result)

            time.sleep(0.2)  # Wait between chunks
    return results


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
