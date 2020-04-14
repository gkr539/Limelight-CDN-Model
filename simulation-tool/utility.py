#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:00:49 2020

@author: gouthamkrs
"""
import json
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import mplcursors
#from pymongo import MongoClient

#client = MongoClient("mongodb+srv://cdnsimulation:limelightcdn@cdn-simulation-b1bz7.mongodb.net/test?retryWrites=true&w=majority")
#db = client.test
#db = client['cdnsimulation']

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
         for i in workloads[workload]["requests"]:
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

def storeObjectInDB(collection,data,db):
    coll = db[collection]
    coll.insert_many(data)

def storeInputObjectsInDB(collections,inputs,db):
    for collection,ip in zip(collections,inputs):
        storeObjectInDB(collection,[ip],db)
        

def deleteDataInCollections(collections,db):
    for coll in collections:
        coll=db[coll]
        coll.remove() 
        
collections=["simulation_input","requests","cacheservers","assets","clients","origins","workloads","systemstate"]


plt.style.use('ggplot')



def live_plotter(x_vec,y1_data,line1,xlabel,ylabel,title,xlim,ylim,identifier='',pause_time=0.01):
    if line1==[]:
        plt.ion()
        fig = plt.figure(figsize=(5,4))
        ax = fig.add_subplot(111)
        ax.set_xlim(0, xlim+1)
        ax.set_ylim(0, ylim)

        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        line1, = ax.plot(x_vec,y1_data,'-o',alpha=0.8,) 
    
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        #mplcursors.cursor(hover=True)
        mplcursors.cursor(hover=True)
    line1.set_data(x_vec, y1_data)
    plt.pause(pause_time)
#    print(x_vec)
#    print(len(y1_data))
#    if(len(x_vec)!=0) and (x_vec[-1]==xlim):
#        print("xxxxx")
#       # plt.savefig('output/'+workload+'/visualization/%s.png' %title)
#        plt.show(block=True)
#        plt.ioff()
#    
    return line1
#deleteDataInCollections(collections,db)