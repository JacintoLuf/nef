import asyncio
import os
import json
import signal
import paramiko
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

# SSH function to execute remote commands using Paramiko
def ssh_execute(ip, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout, stderr

# # Start tcpdump on remote machine
# def start_tcpdump(tcpdump_ip, username, password, capture_file):
#     print(f"Starting tcpdump on {tcpdump_ip}...")
#     cmd = f"sudo tcpdump -i any -w {capture_file}"
#     ssh_execute(tcpdump_ip, username, password, cmd)

# # Stop any running process
# def stop_process(remote_ip, username, password, process_name):
#     print(f"Stopping {process_name} on {remote_ip}...")
#     cmd = f"sudo pkill {process_name}"
#     ssh_execute(remote_ip, username, password, cmd)

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
    cmd = f"sudo kill {str(process.pid)}"
    os.system(cmd)
    try:
        process.terminate()  # Send SIGTERM
    except ProcessLookupError:
        pass
    print("tcpdump stopped.")

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
        if response.headers['location']:
            parsed_url = urlparse(response.headers['location'])
            modified_url = urlunparse((parsed_url.scheme, nef_ip, parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
            print(f"Subscription location: {modified_url}")
            async with httpx.AsyncClient(http1=False, http2=True) as client:
                res = await client.delete(
                    url=modified_url,
                    headers=headers
                )
            print(f"Subscription delete response: {res.status_code} - {res.text}")
        return response
    except httpx.HTTPStatusError as e:
        print(f"Failed request. Error: {e!r}")
        return None
    except Exception as e:
        print(f"Error request: {e!r}")
        return None

def initialize_json():
    return {
        'open5gs': {'mon_c': [],'mon_d': [],'ti_c': [],'ti_d': [],'qos_c': [],'qos_d': []},
        'free5gc': {'mon_c': [],'mon_d': [],'ti_c': [],'ti_d': [],'qos_c': [],'qos_d': []}
    }

def write_json(file_path, data_json):
    with open(file_path, "w") as file:
        json.dump(data_json, file, indent=4)

def open_or_create_json():
    file_path = os.path.join(base_dir, "times", "times.json")
    print(f"Opening JSON file: {file_path}")

    if not os.path.exists(file_path):
        print("File does not exist. Creating a new one...")
        data_json = initialize_json()
        write_json(file_path, data_json)
        return data_json

    try:
        with open(file_path, "r") as file:
            data_json = json.load(file)

        if not isinstance(data_json, dict):
            raise json.JSONDecodeError("Invalid format", "", 0)

    except (json.JSONDecodeError, FileNotFoundError):
        print("Empty or invalid JSON file. Resetting...")
        data_json = initialize_json()
        write_json(file_path, data_json)
    return data_json

def write_to_json(key, val):
    print(f"Writing to json: {key} - {val}")
    data_json = open_or_create_json()
    data_json[core][key].append(val)
    if core in data_json and key in data_json[core]:
        data_json[core][key].append(val)
        write_json("times.json", data_json)
    else:
        print(f"Error: {core} or {key} not found in JSON structure!")

# Main test function
async def run_test(test_type: str, test_file: str):
    # Capture file for tcpdump
    files_count=len([name for name in os.listdir(tcpdump_folder) if os.path.isfile(os.path.join(tcpdump_folder, name)) and test_type in name])
    capture_file = f'{test_type}_{files_count}_{core}.pcap'
    print(f"Capture file: {capture_file}")

    # Start tcpdump on core machine
    # machine_ip = '10.255.35.205' if core == "free5gc" else "10.255.38.50"
    # machine_usr = 'ubuntu' if core == "free5gc" else 'nef'
    # machine_pwd = '1234'
    # tcpdump_thread = Thread(target=start_tcpdump, args=(machine_ip,machine_usr,machine_pwd,capture_file))
    # tcpdump_thread.start()

    tcpdump_process = await start_tcpdump(capture_file)

    try:
        response = await send_request(test_type, test_file)
        await stop_tcpdump(tcpdump_process)
    except Exception as e:
        print(f"Error: {e!r}")
        await stop_tcpdump(tcpdump_process)

    if response:
        # Save time results to file
        if response.headers['X-ElapsedTime-Header']:
            elapsed_time_header = response.headers['X-ElapsedTime-Header']
            print(f"elapsed time header: {response.headers['X-ElapsedTime-Header']}s")
            write_to_json(test_type, elapsed_time_header)

        print("Test finished. Results collected.")
    else:
        print("Test failed. No response received.")

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
            inp = 2
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
                test_file = "qci_mod.json" if inp == 1 else "qos_mod.json"
            elif test_type == "ti_c":
                test_file = "ti_open.json" if core == "open5gs" else "ti_free.json"

        start = False if str(input("Start? Y/n\n")).strip().lower() == "n" else True
        if start:
            asyncio.run(run_test(test_type, test_file))

        run = False if str(input("Run again? Y/n\n")).strip().lower() == "n" else True

    print("All tasks completed.")
