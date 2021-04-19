import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# https://wiki.linuxfoundation.org/networking/netem


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
    pcktLoss = [10 * loss for loss in range(10)]
    for loss in range(10):
        packetLoss(pcktLoss[loss])
        # run client

        # get throughput
        f = open("client-stats.txt", "r")
        totalTime, sz = None, None
        for line in f.readlines():
            vals = [float(i) for i in line.split(" ")]
            sz = vals[0]
            totalTime = vals[1]
        throughput.append(sz / totalTime)

    axis.plot(pcktLoss, throughput)
    axis.set_title("Throughput vs Packet Loss")


def plot_delay(axis):
    throughput = []
    pcktDelay = [10 * delay for delay in range(10)]  # delay in ms
    for delay in range(10):
        packetDelay(pcktDelay[delay])
        # get throughput

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
        packetCorrupt(pcktCorrput[corrput])

        # get throughput
        f = open("client-stats.txt", "r")
        totalTime, sz = None, None
        stats = f.read().split(" ")
        totalTime = float(stats[1])
        sz = int(stats[0])
        throughput.append(sz / totalTime)
    axis.plot(pcktCorrput, throughput)
    axis.set_title("Throughput vs Packet Corrupt")


if __name__ == "__main__":
    figure, axis = plt.subplots(1, 1)
    plot_loss(axis)
    plt.savefig("lossPlot.png", bbox_inches="tight")
    reset_conditions()
    plot_delay(axis)
    plt.savefig("delayPlot.png", bbox_inches="tight")
    reset_conditions()
    plot_delay(axis)
    plt.savefig("reorderPlot.png", bbox_inches="tight")
    reset_conditions()
    plot_delay(axis)
    plt.savefig("corruptPlot.png", bbox_inches="tight")
    reset_conditions()
