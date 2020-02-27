#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# @ModuleName : utils
# @Function : 
# @Author : azson
# @Time : 2020/1/8 15:59
'''

import time, json
from matplotlib import pyplot as plt
import numpy as np

def get_ms_time(rate=1000):

    return time.time()*rate


class Block(object):

    def __init__(self,
                 priority=0,
                 block_id=-1,
                 bytes_size=200000,
                 deadline=200,
                 timestamp=None):

        self.priority = priority
        self.block_id = block_id
        self.size = bytes_size
        self.deadline = deadline
        self.timestamp = timestamp if not timestamp is None else get_ms_time()
        # emulator params
        self.queue_ms = -1
        self.propagation_ms = -1
        self.transmition_ms = -1

        # log params
        self.finish_timestamp = -1
        self.miss_ddl = 0


    def get_cost_time(self):

        return self.queue_ms + self.transmition_ms + self.propagation_ms


    def __str__(self):

        return str(self.__dict__)


class Package(object):

    def __init__(self,
                 create_time,
                 next_hop,
                 block_id,
                 offset,
                 package_id,
                 payload,
                 package_size=1500,
                 deadline=0.2,
                 package_type="S",
                 drop = False,
                 send_delay=.0,
                 queue_delay=.0
                 ):
        self.package_type = package_type
        self.create_time = create_time
        self.next_hop = next_hop
        self.block_id = block_id
        self.offset = offset
        self.package_id = package_id
        self.payload=payload
        self.package_size=package_size
        self.deadline = deadline
        self.drop = drop

        self.send_delay = send_delay
        self.queue_delay = queue_delay
        self.propagation_delay = 0.0002


    def parse(self):

        return [self.package_type,
                self.next_hop,
                self.queue_delay,
                self.drop,
                self.queue_delay,
                self.package_id]


    def trans2dict(self):
        print_data = {
            "Type": self.package_type,
            "Position": self.next_hop,
            "Send_delay": self.send_delay,
            "Queue_delay": self.queue_delay,
            "Propagation_delay": self.propagation_delay,
            "Drop": 1 if self.drop else 0,
            "Package_id": self.package_id,
            "Block_id": self.block_id,
            "Create_time": self.create_time,
            "Deadline": self.deadline,
            "Offset" : self.offset,
            "Payload" : self.payload,
            "Package_size" : self.package_size
        }
        return print_data


    def __lt__(self, other):
        return self.create_time < other.create_time


    def __str__(self):
        print_data = self.trans2dict()
        return str(print_data)


def analyze_pcc_emulator(log_file, trace_file=None, rows=20):

    plt_data = []

    with open(log_file, "r") as f:
        for line in f.readlines():
            plt_data.append(json.loads(line.replace("'", '"')))

    plt_data = filter(lambda x:x["Type"]=='A' and x["Position"] == 2, plt_data)
    # priority by package id
    plt_data = sorted(plt_data, key=lambda x:int(x["Package_id"]))

    pic_nums = 3
    data_lantency = []
    data_finish_time = []
    data_drop = []
    data_sum_time = []
    data_miss_ddl = []
    for idx, item in enumerate(plt_data):
        if item["Type"] == 'A':
            data_lantency.append(item["Queue_delay"])
            data_finish_time.append(item["Time"])
            data_sum_time.append(item["Send_delay"] + item["Queue_delay"] + item["Propagation_delay"])
            if item["Drop"] == 1:
                data_drop.append(len(data_finish_time)-1)
            if item["Deadline"] < data_sum_time[-1]:
                data_miss_ddl.append(len(data_finish_time)-1)

    plt.figure(figsize=(20, 5*pic_nums))
    # plot latency distribution
    ax = plt.subplot(pic_nums, 1, 1)
    ax.set_title("Acked package latency distribution", fontsize=30)
    ax.set_ylabel("Latency / s", fontsize=20)
    ax.set_xlabel("Time / s", fontsize=20)
    ax.scatter(data_finish_time, data_lantency, label="Latency")
    # plot average latency
    ax.plot([0, data_finish_time[-1] ], [np.mean(data_lantency)]*2, label="Average Latency",
            c='r')
    plt.legend(fontsize=20)
    ax.set_xlim(data_finish_time[0] / 2, data_finish_time[-1] * 1.5)

    # plot miss deadline rate block
    ax = plt.subplot(pic_nums, 1, 2)
    ax.set_title("Acked package lost distribution", fontsize=30)
    ax.set_ylabel("Latency / s", fontsize=20)
    ax.set_xlabel("Time / s", fontsize=20)
    ax.scatter([data_finish_time[idx] for idx in data_drop],
                    [data_lantency[idx] for idx in data_drop], label="Drop")
    ax.scatter([data_finish_time[idx] for idx in data_miss_ddl],
                    [data_lantency[idx] for idx in data_miss_ddl], label="Miss_deadline")
    plt.legend(fontsize=20)
    ax.set_xlim(data_finish_time[0] / 2, data_finish_time[-1] * 1.5)

    # plot latency distribution
    ax = plt.subplot(pic_nums, 1, 3)
    ax.set_title("Acked package life time distribution", fontsize=30)
    ax.set_ylabel("Latency / s", fontsize=20)
    ax.set_xlabel("Time / s", fontsize=20)
    ax.set_ylim(-np.min(data_sum_time)*2, np.max(data_sum_time)*2)

    ax.scatter(data_finish_time, data_sum_time, label="Latency")
    # plot average latency
    ax.plot([0, data_finish_time[-1]], [np.mean(data_sum_time)] * 2, label="Average Latency",
            c='r')
    plt.legend(fontsize=20)
    ax.set_xlim(data_finish_time[0]/2, data_finish_time[-1]*1.5)

    # plot bandwith
    if trace_file:
        max_time = data_finish_time[-1]
        trace_list = []
        with open(trace_file, "r") as f:
            for line in f.readlines():
                trace_list.append(list(
                    map(lambda x: float(x), line.split(","))
                ))

        st = 0
        for idx in range(len(trace_list)):
            if trace_list[idx][0] > max_time:
                break
            plt.plot([st, trace_list[idx][0]], [len(plt_data) + 1] * 2, '--',
                     linewidth=5)
            st = trace_list[idx][0]

        if trace_list[-1][0] < max_time:
            plt.plot([st, max_time], [len(plt_data) + 1] * 2, '--',
                 label="Different Bandwith", linewidth=5)

    plt.tight_layout()

    plt.savefig("output/pcc_emulator-analysis.jpg")


def check_solution_format(input):

    if not isinstance(input, dict):
        raise TypeError("The return value should be a dict!")

    keys = ["cwnd", "send_rate"]
    for item in keys:
        if not item in input.keys():
            raise ValueError("Key %s should in the return dict!" % (item))

    return input


def get_emulator_info(sender_mi):

    event = {}
    event["Name"] = "Step"
    # event["Target Rate"] = sender_mi.target_rate
    event["Send Rate"] = sender_mi.get("send rate")
    event["Throughput"] = sender_mi.get("recv rate")
    event["Latency"] = sender_mi.get("avg latency")
    event["Loss Rate"] = sender_mi.get("loss ratio")
    event["Latency Inflation"] = sender_mi.get("sent latency inflation")
    event["Latency Ratio"] = sender_mi.get("latency ratio")
    event["Send Ratio"] = sender_mi.get("send ratio")
    # event["Cwnd"] = sender_mi.cwnd
    # event["Cwnd Used"] = sender_mi.cwnd_used

    return event


if __name__ == '__main__':

    log_package_file = "output/pcc_emulator_package.log"
    analyze_pcc_emulator(log_package_file)