import sys
import subprocess as sub

num = 1
if sys.argv:
    num = int(sys.argv[1])

for i in range(num):
    p = sub.Popen(('iperf3', '-c', '10.255.44.44', '-B', f'10.46.0.3'), stdout=sub.DEVNULL)

