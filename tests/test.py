import asyncio
import os
import json
import paramiko
import httpx
from threading import Thread

# Variables
core = None
nef_ip = None
results = []
results_txt = []
tests = {
    'mon_c': [f'http://{nef_ip}/3gpp-monitoring-event/v1/test/subscriptions'],
    # 'mon_d': [f'http://{nef_ip}/3gpp-as-session-with-qos/v1/test/subscriptions/'],
    'ti_c': [f'http://{nef_ip}/3gpp-traffic-influence/v1/test/subscriptions'],
    # 'ti_d': [f'http://{nef_ip}/3gpp-traffic-influence/v1/test/subscriptions/'],
    'qos_c': [f'http://{nef_ip}/3gpp-as-session-with-qos/v1/test/subscriptions'],
    # 'qos_d': [f'http://{nef_ip}/3gpp-as-session-with-qos/v1/test/subscriptions/']
}

base_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory

tcpdump_folder = os.path.join(base_dir, 'tcpdumps')
if not os.path.exists(tcpdump_folder):
    os.makedirs(tcpdump_folder)

times_folder = os.path.join(base_dir, 'times')
if not os.path.exists(times_folder):
    os.makedirs(tcpdump_folder)

# SSH function to execute remote commands using Paramiko
def ssh_execute(ip, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout, stderr

# Start tcpdump on remote machine
def start_tcpdump(tcpdump_ip, username, password, capture_file):
    print(f"Starting tcpdump on {tcpdump_ip}...")
    cmd = f"sudo tcpdump -i any -w {capture_file}"
    ssh_execute(tcpdump_ip, username, password, cmd)

# HTTP request
async def send_request(request: str, test_file: str):
    print(f"Request for {request}")
    print(f"Test file: {test_file}")
    endpoint = tests[request][0]
    file_path = os.path.join(base_dir, "messages", test_file)
    with open(file_path, 'r') as file:
        data = json.load(file)

    try:
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                endpoint,
                data=data
            )
        return response
    except httpx.HTTPStatusError as e:
        print(f"Failed request. Error: {e!r}")
        return None
    except Exception as e:
        print(f"Error request: {e!r}")
        return None

# Stop any running process
def stop_process(remote_ip, username, password, process_name):
    print(f"Stopping {process_name} on {remote_ip}...")
    cmd = f"sudo pkill {process_name}"
    ssh_execute(remote_ip, username, password, cmd)

def open_or_create_json():
    if os.path.exists("times.json"):
        with open("times.json", "r") as file:
            try:
                data_json = json.load(file)
            except json.JSONDecodeError:
                print("empty or invalid dictionary")
                data_json = {
                    'open5gs': {
                        'mon_c': [],
                        'mon_d': [],
                        'ti_c': [],
                        'ti_d': [],
                        'qos_c': [],
                        'qos_d': []
                    },
                    'free5gc': {
                        'mon_c': [],
                        'mon_d': [],
                        'ti_c': [],
                        'ti_d': [],
                        'qos_c': [],
                        'qos_d': []
                    }
                }
    else:
        data_json = {
            'open5gs': {
                'mon_c': [],
                'mon_d': [],
                'ti_c': [],
                'ti_d': [],
                'qos_c': [],
                'qos_d': []
            },
            'free5gc': {
                'mon_c': [],
                'mon_d': [],
                'ti_c': [],
                'ti_d': [],
                'qos_c': [],
                'qos_d': []
            }
        }
        with open("times.json", "w") as file:
            json.dump(data_json, file, indent=4)
    return data_json

def write_to_json(key, val):
    data_json = open_or_create_json()
    data_json[core][key].append(val)
    with open("times.json", "w") as file:
        json.dump(data_json, file, indent=4)

# Main test function
async def run_test(test_type: str, test_file: str):
    # Capture file for tcpdump
    files_count=len([name for name in os.listdir(tcpdump_folder) if os.path.isfile(os.path.join(tcpdump_folder, name)) and test_type in name])
    capture_file = f'{test_type}_{files_count}_{core}.pcap'
    print(f"Capture file: {capture_file}")

    machine_ip = '10.255.35.205' if core == "free5gc" else "10.255.38.50"
    machine_usr = 'ubuntu' if core == "free5gc" else 'nef'
    machine_pwd = '1234'

    # Start tcpdump on core machine
    tcpdump_thread = Thread(
        target=start_tcpdump, args=(
            machine_ip,
            machine_usr,
            machine_pwd,
            capture_file
        )
    )
    tcpdump_thread.start()

    response = await send_request(test_type, test_file)

    # Stop iperf server and tcpdump after the test
    stop_process(machine_ip, machine_usr, machine_pwd, "tcpdump")

    if response:
        # Save time results to file
        elapsed_time = response.elapsed
        print(f"elapsed time: {elapsed_time}s")
        if response.headers['X-ElapsedTime-Header']:
            elapsed_time_header = response.headers['X-ElapsedTime-Header']
            print(f"elapsed time header: {response.headers['X-ElapsedTime-Header']}s")
        write_to_json('ti_c', elapsed_time)

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

        start = False if str(input("Start? Y/n")).strip().lower() == "n" else True
        if start:
            asyncio.run(run_test(test_type, test_type))

        run = False if str(input("Run again? Y/n")).strip().lower() == "n" else True

    print("All tasks completed.")
