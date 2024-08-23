import os, os.path
import time
import json
import socket
import httpx
import subprocess as sub
# from pexpect import pxssh
from threading import Thread
# from openpyxl import Workbook

dir_path = os.getcwd()
file_type = '.pcap'
files_count = len([f for f in os.listdir(dir_path) if f.endswith(file_type) and os.path.isfile(os.path.join(dir_path, f))])
start = None
end = None
# workbook = Workbook()
# sheet = workbook.active

def start_capture(p):
    start_flag = False
    for row in iter(p.stdout.readline, b''):
        print(f"{row.rstrip()}/t at time {time.time()}")

# def ssh_login(addr, usr, pwd):
#     s = pxssh.pxssh()
#     if not s.login(addr, usr, pwd):
#         print(f"SSH into {addr} session failed on login with user {usr}.")
#         print(str(s))
#         return None
#     else:
#         print(f"SSH into {addr} session login successful with user {usr}")
#         return s

iperf_server = input('iperf server: ')
nef_ip = input('nef addr: ')
test_type = input('test TI(1) or QoS(0): ')
test_param = input('test params: ')
ueransim_addr = input('address of ueransim machine')

if test_type == 1:
    endpoint = nef_ip+'/3gpp-traffic-influence/v1/test/subscriptions'
else:
    endpoint = nef_ip+'/3gpp-as-session-with-qos/v1/test/subscriptions'

hostname = socket.gethostname()
ip_addr = socket.gethostbyname(hostname)
print(f'Running test on machinhe {hostname} with ip: {ip_addr}')

start = time.time()
print(f"Starting capture at: {start}")

f_name = f'run{files_count}'
# p = sub.Popen(('sudo', 'tcpdump', f'host {iperf_server}', 'and tcp or udp', '-l', '-w', f'{f_name}.pcap'), stdout=sub.PIPE)
p = sub.Popen(('sudo', 'tcpdump', '-i any', 'icmp', '-l'), stdout=sub.PIPE)
capture_thread = Thread(target=start_capture, args=(p,), daemon=True)
capture_thread.start()

# response = httpx.post(endpoint, json=json.loads(open(dir_path + f'/messages/{test_param}', 'r')))
# print(response)

pp = sub.Popen(('ping 8.8.8.8'), stdout=sub.DEVNULL)
time.sleep(15)
pp.terminate()

p.terminate()
end = time.time()
print(f"Ending capture at: {end} ")

print(f"Elapsed run time: {end - start}")
