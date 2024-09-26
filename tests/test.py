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

core = None
iperf_server = None
nef_ip = None
test_type = None
test_param = None
ueransim_addr = None
ue_addr = '10.45.0.2'
ue_usr = 'u0_a154'
ue_pwd = '1234'
# workbook = Workbook()
# sheet = workbook.active

def define_vars():
    core = str(input('testing core: ') or 'open5gs')
    iperf_server = str(input('iperf server: ') or '10.255.32.102')
    nef_ip = str(input('nef addr: ') or '10.255.38.50:7777')
    test_type = int(input('test TI(1) or QoS(0): ') or 0)
    test_param = str(input('test params: '))
    ueransim_addr = str(input('address of ueransim machine: ') or '10.255.38.49')

def start_capture(p):
    start_flag = False
    for row in iter(p.stdout.readline, b''):
        print(f"{row.rstrip()}/t at time {time.time()}")

def ssh_login(addr, usr, pwd):
    s = pxssh.pxssh()
    if not s.login(addr, usr, pwd):
        print(f"SSH into {addr} session failed on login with user {usr}.")
        print(str(s))
        return None
    else:
        print(f"SSH into {addr} session login successful with user {usr}")
        s.sendline ('iperf3 -c 10.255.32.107 -B 10.46.0.3 -t 0')
        s.prompt()         # match the prompt
        print(s.before)     # print everything before the prompt.
        time.sleep(60)
        s.sendline(chr(3))
        s.prompt()         # match the prompt
        print(s.before)     # print everything before the prompt.
        s.logout()
        return s

config_vars = True
start = False

while not start:
    inp = str(input('config variables? (Y/n)') or 'y')
    if inp == 'y':
        define_vars()
    else:
        inp = str(input('start simulation? (Y/n)') or 'y')
        if inp == 'y':
            start = True

if test_type == 1:
    endpoint = nef_ip+'/3gpp-traffic-influence/v1/test/subscriptions'
else:
    endpoint = nef_ip+'/3gpp-as-session-with-qos/v1/test/subscriptions'

hostname = socket.gethostname()
ip_addr = socket.gethostbyname(hostname)
print(f'Running test on machinhe {hostname} with ip: {ip_addr}')

start = time.time()
print(f"Starting capture at: {start}")

f_name = f'run{files_count}-{core}'
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
