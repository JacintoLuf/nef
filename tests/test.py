# from openpyxl import Workbook
import os
import time
import json
import socket
import paramiko
import httpx
import subprocess as sub
from threading import Thread

# Variables
iperf_server_ip = '10.255.44.44'
iperf_client_ip = '10.45.0.2'
nef_ip = '10.255.38.58:7777'
tcpdump_machine_ip = '10.255.44.44'  # Same as the iperf server (or another remote machine)
test_duration = 90  # Duration of the iperf test in seconds
results = []
results_txt = []

# Specify the directory where results will be saved
results_dir = os.path.join(os.getcwd(), 'captures')
# Ensure the 'results' folder exists
if not os.path.exists(results_dir):
    os.makedirs(results_dir)
files_count =len([name for name in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, name))])

# SSH function to execute remote commands using Paramiko
def ssh_execute(ip, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=username, password=password)
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout, stderr

# Start iperf server on remote machine
def start_iperf_server(server_ip, username, password):
    print(f"Starting iperf3 server on {server_ip}...")
    cmd = "iperf3 -s -D"
    ssh_execute(server_ip, username, password, cmd)

# Run iperf client on the UE (remote machine)
def run_iperf_client(client_ip, username, password, bind_ip=None):
    print(f"Starting iperf3 client on {client_ip}...")
    cmd = f"iperf3 -c {iperf_server_ip} -B {bind_ip} -t {test_duration}"
    stdout, stderr = ssh_execute(client_ip, username, password, cmd)

    throughput_results = []
    for line in stdout:
        results_txt.append(f'{time.time()}#: {line}')
        if "receiver" in line:
            print(f"iperf result: {line.strip()}")
            # Collect throughput information (assuming it's second last item in the line)
            throughput = line.split()[-2]
            throughput_results.append(float(throughput))
    
    return throughput_results

# Start tcpdump on remote machine
def start_tcpdump(tcpdump_ip, username, password, capture_file):
    print(f"Starting tcpdump on {tcpdump_ip}...")
    cmd = f"sudo tcpdump -i any -w {capture_file} icmp"
    ssh_execute(tcpdump_ip, username, password, cmd)

# Change QoS via HTTP request
def change_qos():
    print("Changing QoS...")
    endpoint = f'http://{nef_ip}/3gpp-as-session-with-qos/v1/test/subscriptions'
    qos_message = {}
    with open('captures/qos_mod.json', 'r') as file:
        data = json.load(file)
    
    try:
        response: httpx.Response = httpx.post(endpoint, json=qos_message)
        response.raise_for_status()
        print("QoS successfully changed.")
    except httpx.HTTPStatusError as err:
        print(f"Failed to change QoS. Error: {err}")
    except Exception as e:
        print(f"Error sending QoS update: {e}")

# Stop any running process (iperf3, tcpdump, etc.)
def stop_process(remote_ip, username, password, process_name):
    print(f"Stopping {process_name} on {remote_ip}...")
    cmd = f"sudo pkill {process_name}"
    ssh_execute(remote_ip, username, password, cmd)

# Main test function
def run_test():    
    # Capture file for tcpdump
    capture_file = f'run_{files_count}.pcap'
    
    # Start iperf3 server on remote machine (iperf server)
    iperf_server_thread = Thread(target=start_iperf_server, args=('10.255.44.44', 'nef', '1234'))
    iperf_server_thread.start()

    # Start tcpdump on remote machine (same or different as iperf server)
    tcpdump_thread = Thread(target=start_tcpdump, args=('10.255.32.147', 'nef', '1234', capture_file))
    tcpdump_thread.start()

    # Run iperf3 client from UEs (remote machine)
    iperf_client_thread_1 = Thread(target=lambda: results.append(run_iperf_client('10.45.0.2', '', '')))
    iperf_client_thread_2 = Thread(target=lambda: results.append(run_iperf_client('10.255.38.55', 'nef', '1234', '10.46.0.3')))
    iperf_client_thread_1.start()
    iperf_client_thread_2.start()

    # Wait for 30 seconds and send QoS update
    time.sleep(30)
    # change_qos()

    # Wait for the iperf tests to finish
    iperf_client_thread_1.join()
    iperf_client_thread_2.join()


    # Stop iperf server and tcpdump after the test
    stop_process('10.255.44.44', 'nef', '1234', "iperf3")
    stop_process('10.255.32.147', 'nef', '1234', "tcpdump")

    print("Test finished. Results collected.")

    # Save results to file (for further analysis)
    with open(f"throughput_results_{time.time()}.json", 'w') as f:
        json.dump(results, f)
    with open(f"test_{files_count}.json", 'w') as f:
        for line in results_txt:
            f.write(line + '\n')

if __name__ == '__main__':
    run_test()
    print("All tasks completed.")
