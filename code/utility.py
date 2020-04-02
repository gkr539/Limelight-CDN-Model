#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:00:49 2020

@author: gouthamkrs
"""
import json
import math
from pymongo import MongoClient

client = MongoClient("mongodb+srv://cdnsimulation:limelightcdn@cdn-simulation-b1bz7.mongodb.net/test?retryWrites=true&w=majority")
db = client.test
db = client['cdnsimulation']

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
deleteDataInCollections(collections,db)