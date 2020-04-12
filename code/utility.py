#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:00:49 2020

@author: gouthamkrs
"""
import json
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import mplcursors


def read_json(path):
    
    f = open(path)
    data = json.load(f) 
    temp = {}
    for i in range(len(data)):
        temp[data[i]['id']] = data[i]
    f.close()
    return temp
    
    


def input_workload(filepath):   
     workloads=read_json(filepath)
     dict={}
     for workload in workloads.keys():
         for i in workloads[workload]["Requests"]:
             if workload not in dict:
                 dict[workload]={}
             if int(i["time"]) not in dict[workload]:
                dict[workload][int(i["time"])]=i["request_id"]
     return dict
 
    
    
def timeToTransfer(size, throughput):
    #return time in milli seconds
    #print(size, throughput)  
    time = (size/throughput)*1000
    #print(time)
    return math.ceil(time)

plt.style.use('ggplot')
def live_plotter(x_vec,y1_data,line1,xlabel,ylabel,title,xlim,ylim,identifier='',pause_time=0.01):
    if line1==[]:
        plt.ion()
        fig = plt.figure(figsize=(5,4))
        ax = fig.add_subplot(111)
        ax.set_xlim(0, xlim)
        ax.set_ylim(0, ylim)

        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        line1, = ax.plot(x_vec,y1_data,'-o',alpha=0.8) 
    
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        mplcursors.cursor(hover=True)
        
    
    line1.set_data(x_vec, y1_data)
    plt.pause(pause_time)
    
    return line1