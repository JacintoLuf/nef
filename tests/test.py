import asyncio
import os
import json
import time
# import paramiko
import httpx
from  urllib.parse import urlparse, urlunparse

# Variables
core = None
nef_ip = None
results = []
results_txt = []
tests = None

base_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory

tcpdump_folder = os.path.join(base_dir, 'tcpdumps')
os.makedirs(tcpdump_folder, exist_ok=True)
times_folder = os.path.join(base_dir, 'times')
os.makedirs(times_folder, exist_ok=True)

file_path = os.path.join(base_dir, "times", "times.json")


async def start_tcpdump(capture_file):
    """Start tcpdump asynchronously and return the process."""
    print(f"Starting tcpdump, saving to {capture_file}...")
    process = await asyncio.create_subprocess_exec(
        "sudo", "tcpdump", "-i", "any", "-w", f"tcpdumps/{capture_file}",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    print(f"tcpdump started with PID {process.pid}")
    return process

async def stop_tcpdump(process):
    """Stop the tcpdump process asynchronously."""
    print("Stopping tcpdump...")
    cmd = f"sudo pkill tcpdump"
    os.system(cmd)
    try:
        process.terminate()  # Send SIGTERM
    except ProcessLookupError:
        pass
    print("tcpdump stopped.")

async def delete_tcpdump(capture_file):
    print(f"Deleting tcpdump file {capture_file}...")
    os.remove(os.path.join(tcpdump_folder, capture_file))
    print("File deleted.")

# HTTP request
async def send_request(request: str, test_file: str):
    print(f"Request for {request} endpoint: {tests[request][0]}")
    print(f"Test file: {test_file}")
    endpoint = tests[request][0]
    file_path = os.path.join(base_dir, "messages", test_file)
    with open(file_path, 'r') as file:
        data = json.load(file)
    print(f"Request data: {data}")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    try:
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                data=json.dumps(data)
            )
            print(f"Response: {response.status_code} - {response.text}")
        # sub = response.headers['location']
        if response.headers['location'] or request == "mon_c":
            parsed_url = urlparse(response.headers['location'])
            modified_url = urlunparse((parsed_url.scheme, nef_ip, parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
            print(f"Subscription location: {modified_url}")
            if response.headers["X-ElapsedTime-Header"] and response.headers["core-elapsed-time"]:
                nef_time = response.headers["X-ElapsedTime-Header"]-response.headers["core-elapsed-time"]
                write_to_json(request, [response.headers['X-ElapsedTime-Header'], nef_time])
            else:
                write_to_json(request, [response.elapsed.total_seconds() * 1000, None])
            if request != "mon_c":
                async with httpx.AsyncClient(http1=False, http2=True) as client:
                    res = await client.get(
                        url=modified_url,
                        headers=headers
                    )
                print(f"Subscription get response: {res.status_code} - {res.text}")
                if res.status_code == 204:
                    delete_req = request.split("_")[0]+"_g"
                    if res.headers['X-ElapsedTime-Header']:
                        write_to_json(delete_req, [res.headers['X-ElapsedTime-Header'], None])
                    else:
                        write_to_json(delete_req, [res.elapsed.total_seconds() * 1000, None])

                async with httpx.AsyncClient(http1=False, http2=True) as client:
                    res = await client.delete(
                        url=modified_url,
                        headers=headers
                    )
                print(f"Subscription delete response: {res.status_code} - {res.text}")
                if res.status_code == 204:
                    delete_req = request.split("_")[0]+"_d"
                    if res.headers['X-ElapsedTime-Header'] and res.headers["core-elapsed-time"]:
                        nef_time = response.headers["X-ElapsedTime-Header"]-response.headers["core-elapsed-time"]
                        write_to_json(delete_req, [res.headers['X-ElapsedTime-Header'], nef_time])
                    else:
                        write_to_json(delete_req, [res.elapsed.total_seconds() * 1000, None])
        return response
    except httpx.HTTPStatusError as e:
        print(f"Failed request. Error: {e!r}")
        return None
    except Exception as e:
        print(f"Error request: {e!r}")
        return None

def initialize_json():
    return {
        'open5gs': {'mon_g': [],'mon_c': [],'mon_d': [],'ti_g': [],'ti_c': [],'ti_d': [],'qos_g': [],'qos_c': [],'qos_d': []},
        'free5gc': {'mon_g': [],'mon_c': [],'mon_d': [],'ti_g': [],'ti_c': [],'ti_d': [],'qos_g': [],'qos_c': [],'qos_d': []}
    }

def write_json(data_json):
    with open(file_path, "w") as file:
        json.dump(data_json, file, indent=4)

def open_or_create_json():
    print(f"Opening JSON file: {file_path}")

    if not os.path.exists(file_path):
        print("File does not exist. Creating a new one...")
        data_json = initialize_json()
        write_json(data_json)
        return data_json

    try:
        with open(file_path, "r") as file:
            data_json = json.load(file)

        if not isinstance(data_json, dict):
            raise json.JSONDecodeError("Invalid format", "", 0)

    except (json.JSONDecodeError, FileNotFoundError):
        print("Empty or invalid JSON file. Resetting...")
        data_json = initialize_json()
        write_json(data_json)
    return data_json

def write_to_json(key, val):
    print(f"Writing to json: {key} - {val}")
    data_json = open_or_create_json()
    if core in data_json and key in data_json[core]:
        data_json[core][key].append(val)
        write_json(data_json)
    else:
        print(f"Error: {core} or {key} not found in JSON structure!")

# Main test function
async def run_test(test_type: str, test_file: str):
    # Capture file for tcpdump
    files_count=len([name for name in os.listdir(tcpdump_folder) if os.path.isfile(os.path.join(tcpdump_folder, name)) and test_file in name])
    capture_file = f'{core}_{test_type}_{test_file}_{files_count}.pcap'
    print(f"Capture file: {capture_file}")

    tcpdump_process = await start_tcpdump(capture_file)

    try:
        response = await send_request(test_type, test_file)
    except Exception as e:
        print(f"Error: {e!r}")
    
    await stop_tcpdump(tcpdump_process)
    try:
        if (not response or 'location' not in response.headers) and test_type != "mon_c":
            await delete_tcpdump(capture_file)
    except Exception as e:
        await delete_tcpdump(capture_file)

    print("Test finished. Results collected.")

if __name__ == '__main__':
    run = True
    while run:
        while not core:
            try:
                inp = int(input("core:\n(1)OPEN5GS\t(2)free5gc\n"))
            except Exception as e:
                inp = 1
            core = "free5gc" if inp == 2 else "open5gs"
            nef_ip = '10.255.32.164:7777' if core == "free5gc" else "10.255.38.50:7777"
            tests = {
                'mon_c': [f'http://{nef_ip}/3gpp-monitoring-event/v1/test/subscriptions'],
                # 'mon_d': [f'http://{nef_ip}/3gpp-as-session-with-qos/v1/test/subscriptions/'],
                'ti_c': [f'http://{nef_ip}/3gpp-traffic-influence/v1/test/subscriptions'],
                # 'ti_d': [f'http://{nef_ip}/3gpp-traffic-influence/v1/test/subscriptions/'],
                'qos_c': [f'http://{nef_ip}/3gpp-as-session-with-qos/v1/test/subscriptions'],
                # 'qos_d': [f'http://{nef_ip}/3gpp-as-session-with-qos/v1/test/subscriptions/']
            }

        test_types = [key for key in tests.keys()]
        try:
            inp = int(input("test type:\n"+" ".join(f"({index+1}){item}" for index, item in enumerate(test_types))+"\n"))
        except Exception as e:
            inp = 1
        test_type = test_types[inp-1]

        test_file = None
        while not test_file:
            if test_type == "mon_c":
                test_file = "mon_evt.json"
            elif test_type == "qos_c":
                try:
                    inp = int(input("(1)QCI\t(2)QOS\n"))
                except Exception as e:
                    inp = 1
                if core == "open5gs":
                    test_file = "qci_mod.json" if inp == 1 else "qos_mod.json"
                else:
                    test_file = "qci_mod_free.json" if inp == 1 else "qos_mod_free.json"
            elif test_type == "ti_c":
                test_file = "ti_open.json" if core == "open5gs" else "ti_free.json"

        start = False if str(input("Start? Y/n\n")).strip().lower() == "n" else True
        if start:
            asyncio.run(run_test(test_type, test_file))

        run = False if str(input("Run again? Y/n\n")).strip().lower() == "n" else True

    print("All tasks completed.")
