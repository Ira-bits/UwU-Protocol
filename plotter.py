import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import subprocess

# https://wiki.linuxfoundation.org/networking/netem


def runApplication():
    os.system(f"fuser -k 8000/udp")
    p = os.popen("/usr/bin/python3 /home/divyanshu/net/a2/server.py")
    os.system("/home/divyanshu/net/a2/application LICENSE")
    os.system(f"fuser -k 8000/udp")


def packetLoss(packet_loss):
    os.system(f"tc qdisc change dev lo root netem loss {packet_loss}%")


def packetDelay(delay: int):
    os.system(f"tc qdisc change dev lo root netem delay {delay}ms")


def packetReorder(num: int):
    os.system(f"tc qdisc change dev lo root netem reorder {num}")


def packetCorruption(percentage: int):
    os.system(f"tc qdisc change dev lp root netem corrupt {percentage}%")


def reset_conditions():
    os.system("tc qdisc del dev lo root netem")
    os.system("tc qdisc add dev lo root netem")


def plot_loss(axis):
    throughput = []
    overallstats = ""
    pcktLoss = [10 * loss for loss in range(7)]
    for loss in range(7):
        packetLoss(pcktLoss[loss])
        # run client
        runApplication()

        # get throughput
        f = open("client-stats.txt", "r")
        totalTime, sz = None, None
        stats = f.read().split(" ")
        totalTime = float(stats[1])
        overallstats += str(f"\n{totalTime}")
        sz = int(stats[0])
        throughput.append(sz / totalTime)
    axis.plot(pcktLoss, throughput)
    axis.set_title("Throughput vs Packet Loss")
    print(overallstats)


def plot_delay(axis):
    throughput = []
    pcktDelay = [10 * delay for delay in range(10)]  # delay in ms
    for delay in range(10):
        packetDelay(pcktDelay[delay])
        # get throughput
        runApplication()
        f = open("client-stats.txt", "r")
        totalTime, sz = None, None
        for line in f.readlines():
            vals = [float(i) for i in line.split(" ")]
            sz = vals[0]
            totalTime = vals[1]
        throughput.append(sz / totalTime)
    axis.plot(pcktDelay, throughput)
    axis.set_title("Throughput vs Packet Delay")


def plot_reorder(axis):
    throughput = []
    pcktReorder = [10 * reorder for reorder in range(10)]
    for reorder in range(10):

        packetReorder(pcktReorder[reorder])
        # get throughput
        runApplication()
        f = open("client-stats.txt", "r")
        totalTime, sz = None, None
        for line in f.readlines():
            vals = [float(i) for i in line.split(" ")]
            sz = vals[0]
            totalTime = vals[1]
        throughput.append(sz / totalTime)
    axis.plot(pcktReorder, throughput)
    axis.set_title("Throughput vs Packet Reorder")


def plot_corrupt(axis):
    throughput = []
    pcktCorrput = [10 * corrput for corrput in range(10)]
    for corrput in range(10):
        packetCorruption(pcktCorrput[corrput])
        # get throughput
        runApplication()
        f = open("client-stats.txt", "r")
        totalTime, sz = None, None
        stats = f.read().split(" ")
        totalTime = float(stats[1])
        # overallstats += str(f"\n{totalTime}")
        sz = int(stats[0])
        throughput.append(sz / totalTime)
    axis.plot(pcktCorrput, throughput)
    axis.set_title("Throughput vs Packet Corrupt")


if __name__ == "__main__":
    figure, axis = plt.subplots(1, 1)
    # plot_loss(axis)
    # plt.savefig("lossPlot.png", bbox_inches="tight")
    # reset_conditions()
    # plot_delay(axis)
    # plt.savefig("delayPlot.png", bbox_inches="tight")
    # reset_conditions()
    # plot_reorder(axis)
    # plt.savefig("reorderPlot.png", bbox_inches="tight")
    reset_conditions()
    plot_corrupt(axis)
    plt.savefig("corruptPlot.png", bbox_inches="tight")
    reset_conditions()
