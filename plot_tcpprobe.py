from helper import *
from collections import defaultdict
import argparse
import matplotlib as m
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('--sport', help="Enable the source port filter (Default is dest port)", 
                   action='store_true', dest="sport", default=False)
parser.add_argument('-p', '--port', dest="port", default='5001')
parser.add_argument('-f', dest="files", nargs='+', required=True)
parser.add_argument('-o', '--out', dest="out", default=None)
parser.add_argument('-H', '--histogram', dest="histogram",
                    help="Plot histogram of sum(cwnd_i)",
                    action="store_true",
                    default=False)
args = parser.parse_args()

# Sửa các hàm first và second để trả về list thay vì generator
def first(lst):
    return list(map(lambda e: e[0], lst))

def second(lst):
    return list(map(lambda e: e[1], lst))

def parse_file(f):
    num_fields = 10
    linux_ver = os.uname()[2].split('.')[:2]
    ver_1, ver_2 = [int(ver_i) for ver_i in linux_ver]
    if ver_1 == 3 and ver_2 >= 12:
        num_fields = 11
        
    times = defaultdict(list)
    cwnd = defaultdict(list)
    srtt = []
    
    with open(f, 'r') as file:
        for l in file:
            fields = l.strip().split(' ')
            if len(fields) != num_fields:
                break
                
            if not args.sport:
                if fields[2].split(':')[1] != args.port:
                    continue
            else:
                if fields[1].split(':')[1] != args.port:
                    continue
                    
            sport = int(fields[1].split(':')[1])
            times[sport].append(float(fields[0]))
            c = int(fields[6])
            cwnd[sport].append(c * 1480 / 1024.0)
            srtt.append(int(fields[-1]))
            
    return times, cwnd

added = defaultdict(int)
events = []

def plot_cwnds(ax):
    global events
    for f in args.files:
        times, cwnds = parse_file(f)
        for port in sorted(cwnds.keys()):
            t = times[port]
            cwnd = cwnds[port]
            # Chuyển zip thành list
            events.extend(list(zip(t, [port]*len(t), cwnd)))
            ax.plot(t, cwnd)
    events.sort()

total_cwnd = 0
cwnd_time = []
min_total_cwnd = 10**10
max_total_cwnd = 0
totalcwnds = []

# Thiết lập kích thước figure
m.rc('figure', figsize=(16, 6))
fig = plt.figure()
plots = 1
if args.histogram:
    plots = 2

axPlot = fig.add_subplot(1, plots, 1)
plot_cwnds(axPlot)

for (t,p,c) in events:
    if added[p]:
        total_cwnd -= added[p]
    total_cwnd += c
    cwnd_time.append((t, total_cwnd))
    added[p] = c
    totalcwnds.append(total_cwnd)

# Vẽ đồ thị tổng
axPlot.plot(first(cwnd_time), second(cwnd_time), lw=2, label="$\sum_i W_i$")
axPlot.grid(True)
axPlot.set_xlabel("seconds")
axPlot.set_ylabel("cwnd KB")
axPlot.set_title("TCP congestion window (cwnd) timeseries")

if args.histogram:
    axHist = fig.add_subplot(1, 2, 2)
    n, bins, patches = axHist.hist(totalcwnds, 50, density=1, 
                                 facecolor='green', alpha=0.75)
    axHist.set_xlabel("bins (KB)")
    axHist.set_ylabel("Fraction")
    axHist.set_title("Histogram of sum(cwnd_i)")

if args.out:
    print('saving to', args.out)
    plt.savefig(args.out)
else:
    plt.show()