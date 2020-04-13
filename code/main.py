#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 22:57:24 2020

@author: gouthamkrs
"""

'''
ENDPOINTS
tctc - tcp connection time cache
cct - cache check time
tcto  - tcp connection time origin
adtc - asset deliver time from cache
oct -  asset check time by origin
adto - asset deliver time from origin
end - if end is 1 then request is processed and asset is delivered 
'''
# add throughput_used to req_status
    #mport os
import shutil

import utility
import collections
from pprint import pprint
import matplotlib.pyplot as plt
from matplotlib import style
import sys
import os
import json
from utility import live_plotter
from matplotlib.ticker import MaxNLocator


req_status = collections.defaultdict(dict)
sim_status = collections.defaultdict(dict)

throughput_status = collections.defaultdict(dict)
throughput_status_time = collections.defaultdict(dict)
cacheServer_status = collections.defaultdict(dict)

stage = {
        0 : 'tctc',
        1 : 'cct',
        2 : 'adtc',
        3: 'tcto',
        4: 'oct'
        }

def checkStage(t,endpoint,req):
    if t < req_status[req][endpoint]:
        return 0
    elif t == req_status[req][endpoint]:
        return 1
    return 2
        

def simulation(t,requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip): 
    #handle new requests if any

    if t in workload_ip.keys():
        new_req = workload_ip[t] 
        for req in new_req:
            req_status[req] = {t : "started"}
            req_status[req]['initiated_at'] = t
            req_status[req]['tctc'] = t + int(simulation_ip['simulation1']['tcp_connection_time'])
            req_status[req]['stage'] = 0
            req_status[req]['completed'] = 0
            req_status[req]['client'] = requests_ip[req]['client']
            req_status[req]['origin'] = requests_ip[req]['origin']
            req_status[req]['asset'] = requests_ip[req]['asset']
            req_status[req]['input_throughput_being_used'] = {}
            req_status[req]['input_throughput_being_used']['client'] = 0
            req_status[req]['input_throughput_being_used']['cacheServer'] = 0
            req_status[req]['output_throughput_being_used'] = {}
            req_status[req]['output_throughput_being_used']['origin'] = 0
            req_status[req]['output_throughput_being_used']['cacheServer'] = 0
            
    #handle started requests    
    if req_status:
        temp_keys = []
        temp_key1 = []
        for r in req_status.keys():
            if req_status[r]['completed'] == 0:
                v1 = req_status[r].get('adtc1',0)
                v2 = req_status[r].get('adtc',0)
                v3 = req_status[r].get('cct',0)
                if v1 != 0:
                    temp_key1.append((v1,r))
                elif v2 !=0:
                    temp_key1.append((v2,r))
                else:
                    temp_key1.append((0,r))
                    
                    
                #print(req_status[r].get('adtc1'))
                if  v1 != 0:
                    v2 = req_status[r].get('adtc',0)
                    temp_keys.append((v2,r))
                else:
                    temp_keys.append((v1,r))
                v3 = req_status[r].get('cct',0)
       
        #print(t, temp_keys)     
        temp_keys.sort(key = lambda x : x[0])
        temp_key1.sort(key = lambda x : x[0])
        print(t, temp_key1)
        
        fin_keys = [i[1] for i in temp_key1] 
        for req in fin_keys:             
            
            max_connections_cache = cacheServer_ip['cacheserver1']["max_connections"]
    
            if req_status[req]['completed'] == 0:
                
                '''
                if not checkStage(t,'tctc',req,'tcp connection established to cache server '):
                    continue
                elif checkStage(t,'tctc',req) == 1 :
                    req_status[req][t] = 'tcp connection established to cache server'
                    # add cct endpoint - done
                    req_status[req]['cct'] = t + int(cacheServer_ip['cacheserver1']["time_to_check_cache"])
                '''
                    
                
                if req_status[req]['stage'] ==  0:
                    if t < req_status[req]['tctc']:
                        req_status[req][t] = 'Establishing TCP connection to cache server'
                        continue
                    elif t == req_status[req]['tctc']:
                        max_connections_client = clients_ip[requests_ip[req]['client']]['max_connections']
                        if (sim_status['inbound_connections_cacheServer'] + sim_status['outbound_connections_cacheServer'] < max_connections_cache) and (sim_status['connections_client'][requests_ip[req]['client']] < max_connections_client):
                            req_status[req][t] = 'tcp connection established to cache server'
                            req_status[req]['cct'] = t + int(cacheServer_ip['cacheserver1']["time_to_check_cache"])
                            # start using throughput   at
                            new_t = t + int(cacheServer_ip['cacheserver1']["time_to_check_cache"])
                            if requests_ip[req]['asset'] in cacheServer_ip['cacheserver1']['cached_assets_id']:
                                client_id = (clients_ip[requests_ip[req]['client']]['id'])
                                if len(throughput_status_time[client_id]) == 0:
                                    throughput_status_time[client_id][new_t] =throughput_status_time[client_id].get(new_t,0) +  1
                                    throughput_status_time[client_id]['old'] = new_t
                                    
                                else:
                                    if throughput_status_time[client_id]['old'] > new_t:
                                        throughput_status_time[client_id]['old'] = new_t
                                    req_count = 1
                                    for key in throughput_status_time[client_id]:
                                        if key != 'old' and key != 'temp_adto' and key <= new_t:
                                            req_count += throughput_status_time[client_id][key]
                                        if key != 'old' and key != 'temp_adto' and key > new_t:
                                            throughput_status_time[client_id][key] +=1
                                    throughput_status_time[client_id][new_t] = req_count
                            
                            req_status[req]['stage'] = 1
                            sim_status['inbound_connections_cacheServer'] += 1
                            cacheServer_status['cacheserver1']['active_inbound_connections'] +=1
                            sim_status['connections_client'][requests_ip[req]['client']] += 1
                        else:
                            
                            req_status[req]['tctc'] += 1
                            req_status[req][t]="Max connections reached. Waiting until connections are available" 
                            continue
                            
                                       
                
                if req_status[req]['stage'] ==  1:
                    if t < req_status[req]['cct']:
                        req_status[req][t] = 'Checking for the requested asset in Cache'
                        continue
                    elif t == req_status[req]['cct']:
                        #check if cache present in cache server ( added 'cached_assets_id' in json)
                        if requests_ip[req]['asset'] in cacheServer_ip['cacheserver1']['cached_assets_id']:
                            req_status[req][t] = 'Requested asset present in cache'
                            #check throughput and calculate endpoint to transfer asset to client
                            req_asset_id = requests_ip[req]['asset']
                            asset_size = int(assets_ip[req_asset_id]['size'])
                            cache_throughput = int(cacheServer_ip['cacheserver1']['max_output_throughput'])
                            client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                            #check available throughput-- 
                            available_throughput = min(cache_throughput,client_throughput)
   
                            time_taken = utility.timeToTransfer(asset_size,available_throughput)
                            #print(time_taken)
                            req_status[req]['adtc'] = t + time_taken
                            
                            req_status[req]['size_trasnferred'] = {}
                            req_status[req]['size_trasnferred'][t] = 0
                            cacheServer_status['cacheserver1']['cache_hit'] += 1 
                            req_status[req]['stage'] = 2
                                                       
                        else:
                            req_status[req][t] = 'Requested asset not present in cache'
                            #add tcp endpoint to origin
                            req_status[req]['tcto'] = t + int(simulation_ip['simulation1']['tcp_connection_time'])
                            cacheServer_status['cacheserver1']['cache_miss'] += 1 
                            req_status[req]['stage'] = 3
                    
                                            
                #handle adtc
                if req_status[req]['stage'] ==  2:
                    if t < req_status[req]['adtc']:
                                                                 
                        client_id = (clients_ip[requests_ip[req]['client']]['id'])
                        req_asset_id = requests_ip[req]['asset']
                        asset_size = int(assets_ip[req_asset_id]['size'])  - req_status[req]['size_trasnferred'].get(t,0)
                        cache_throughput = int(cacheServer_ip['cacheserver1']['max_output_throughput'])
                        client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                            #check available throughput-- 
                        available_throughput = min(cache_throughput,client_throughput)
                        te = throughput_status_time[client_id]['old']
                        if t in throughput_status_time[client_id]:
                            n = throughput_status_time[client_id].get(t)
                            throughput_status_time[client_id]['old'] = t
                            
                        else:
                            n = throughput_status_time[client_id][te]
                            

                        throughput_to_use = available_throughput/n
                        req_status[req]['input_throughput_being_used']['client'] = throughput_to_use
                        req_status[req]['output_throughput_being_used']['cacheServer'] = throughput_to_use
                        cacheServer_status['cacheserver1']['output_throughput_used'] = throughput_to_use
                        cacheServer_status['cacheserver1']['output_throughput_available'] = int(cacheServer_ip['cacheserver1']['max_output_throughput']) - throughput_to_use
                        #update req status
                        
                        
                        
                        time_taken = utility.timeToTransfer(asset_size,throughput_to_use)
                        trasnfer_pertick = asset_size / time_taken
                        #print(throughput_to_use, trasnfer_pertick, req, t)
                        #req_status[req]['size_trasnferred'][t+1] = (t+1 - req_status[req]['cct']) * trasnfer_pertick
                        #pprint(req_status[req])
                        req_status[req]['size_trasnferred'][t+1] = req_status[req]['size_trasnferred'][t]  + trasnfer_pertick
                        req_status[req]['adtc'] = t + time_taken 
                        
                        req_status[req][t] = 'Transferring asset to client'
                        continue
                    elif t == req_status[req]['adtc']:
                        req_status[req][t] = 'Asset transferred to client'
                        
                        sim_status['inbound_connections_cacheServer'] -=1
                        cacheServer_status['cacheserver1']['active_inbound_connections'] -= 1
                        sim_status['connections_client'][requests_ip[req]['client']] -= 1
                        client_id = (clients_ip[requests_ip[req]['client']]['id'])  
                        #del throughput_status_time[client_id][req_status[req]['cct']]
                        for key in throughput_status_time[client_id]:
                            if key != 'old' and key != 'temp_adto':
                                if throughput_status_time[client_id][key] > 1:
                                    throughput_status_time[client_id][key] -=1     
                                else:
                                    throughput_status_time[client_id][key] = 0
                        req_status[req]['completed'] = 1
                        req_status[req]['input_throughput_being_used']['client'] = 0
                        req_status[req]['input_throughput_being_used']['cacheServer'] = 0
                        req_status[req]['output_throughput_being_used']['origin'] = 0
                        req_status[req]['output_throughput_being_used']['cacheServer'] = 0
                                                
                                                  
                                             
                        
                if req_status[req]['stage'] >=  3:
                    #if 'tcto' in req_status[req]:
                    if req_status[req]['stage'] == 3:
                        if t < req_status[req]['tcto']:
                            req_status[req][t] = 'Establishing TCP connection to Origin'
                            continue
                        elif t == req_status[req]['tcto']:
                            if (sim_status['connections_origin'][requests_ip[req]['origin']] < int(origin_ip[requests_ip[req]['origin']]["max_connections"]) and (sim_status['outbound_connections_cacheServer'] + sim_status['inbound_connections_cacheServer'] < max_connections_cache)):
                                sim_status['connections_origin'][requests_ip[req]['origin']] += 1
                                sim_status['outbound_connections_cacheServer'] +=1
                                cacheServer_status['cacheserver1']['active_outbound_connections'] += 1
                                req_status[req][t] = 'tcp connection established to origin server'
                                req_status[req]['oct'] = t + int(origin_ip[requests_ip[req]['origin']]['asset_check_time'])
                                req_status[req]['stage'] = 4
                                
                                new_t = t + int(origin_ip[requests_ip[req]['origin']]['asset_check_time'])
                               
                                cacheServer_id = requests_ip[req]['server']
                                if len(throughput_status_time[cacheServer_id]) == 0:                                
                                    throughput_status_time[cacheServer_id][new_t] =throughput_status_time[cacheServer_id].get(new_t,0) +  1
                                    throughput_status_time[cacheServer_id]['old'] = new_t                                    
                                else:                                                              
                                    req_count = 1
                                    for key in throughput_status_time[cacheServer_id]:
                                        if key != 'old':
                                            req_count += throughput_status_time[cacheServer_id][key]
                                    throughput_status_time[cacheServer_id][new_t] = req_count  
                            else:
                                req_status[req]['tcto'] +=1
                                req_status[req][t]="Max connections reached. Waiting until connections are available"
                                continue
                                                        
                            #check throughput and calculate endpoint to trasnfer asset to cache server
                            #assuming asset present in origin server
                    elif req_status[req]['stage'] == 4 :     
                        if t < req_status[req]['oct']:
                            req_status[req][t] = 'Checking for the requested asset in Origin'
                            continue;
                        elif t == req_status[req]['oct']:
                            
                            if requests_ip[req]['asset'] in origin_ip[requests_ip[req]['origin']]['assets']:
                                req_status[req][t] = 'Requested asset present in Origin server'
                                #check throughput and calculate endpoint to transfer asset to cache
                                # without any constraints 
                                #with constraints -- TO DO
                                req_asset_id = requests_ip[req]['asset']
                                asset_size = int(assets_ip[req_asset_id]['size'])
                                cache_throughput1 = int(cacheServer_ip['cacheserver1']['max_input_throughput'])
                                origin_throughput = int(origin_ip[requests_ip[req]['origin']]['max_output_throughput'])
                                #check available throughput--  
                                available_throughput1 = min(cache_throughput1,origin_throughput)
                                time_taken1 = utility.timeToTransfer(asset_size,available_throughput1)
                                req_status[req]['adto'] = t + time_taken1
                                
                                
                                #add to client throughput status 
                                new_t = t + time_taken1
                                
                                client_id = (clients_ip[requests_ip[req]['client']]['id'])
                                if len(throughput_status_time[client_id]) == 0:
                                    throughput_status_time[client_id][new_t] =throughput_status_time[client_id].get(new_t,0) +  1
                                    throughput_status_time[client_id]['old'] = new_t
                                    
                                    
                                else:
                                
                                    req_count1 = 1
                                    for key in throughput_status_time[client_id]:
                                        if key != 'old' and key != 'temp_adto':
                                            req_count1 += throughput_status_time[client_id][key]
                                    throughput_status_time[client_id][new_t] = req_count1
                                #throughput_status_time[client_id]['old1'] = new_t  
                                throughput_status_time[client_id]['temp_adto'] = new_t
                                throughput_status_time['temp_adto'][req] = new_t
                               # print(throughput_status_time)
                               
                                req_status[req]['size_trasnferred'] = {}
                                req_status[req]['size_trasnferred'][t] = 0
                        if 'adto' in req_status[req]:
                            if t < req_status[req]['adto']:
                                cacheServer_id = requests_ip[req]['server']
                                req_asset_id = requests_ip[req]['asset']
                                asset_size = int(assets_ip[req_asset_id]['size'])  - req_status[req]['size_trasnferred'].get(t,0)
                                cache_throughput1 = int(cacheServer_ip['cacheserver1']['max_input_throughput'])
                                origin_throughput = int(origin_ip[requests_ip[req]['origin']]['max_output_throughput'])
                                    #check available throughput-- 
                                available_throughput1 = min(cache_throughput1,origin_throughput)
                            
                                #n = throughput_status_time[client_id].get(t,0) + 1
                                #print(throughput_status_time)
                                te = throughput_status_time[cacheServer_id]['old']
                                if t in throughput_status_time[cacheServer_id]:
                                    n = throughput_status_time[cacheServer_id].get(t)
                                    throughput_status_time[cacheServer_id]['old'] = t
                                    
                                else:
                                    n = throughput_status_time[cacheServer_id][te]
                                    
                                #n = throughput_status_time[client_id].get(t,1)
                                throughput_to_use1 = available_throughput1/n
                                
                                
                                req_status[req]['input_throughput_being_used']['cacheServer'] = throughput_to_use1
                                req_status[req]['output_throughput_being_used']['origin'] = throughput_to_use1
                                total_cs_throughput_use=0
                                for i in req_status.keys():
                                    total_cs_throughput_use+=req_status[i]['input_throughput_being_used']['cacheServer']
                                cacheServer_status['cacheserver1']['input_throughput_used'] = total_cs_throughput_use
                                cacheServer_status['cacheserver1']['input_throughput_available'] = int(cacheServer_ip['cacheserver1']['max_input_throughput']) - throughput_to_use1
   
                                
                                time_taken1 = utility.timeToTransfer(asset_size,throughput_to_use1)
                                trasnfer_pertick1 = asset_size / time_taken1
                                #print(throughput_to_use, trasnfer_pertick, req, t)
                                #req_status[req]['size_trasnferred'][t+1] = (t+1 - req_status[req]['cct']) * trasnfer_pertick
                                req_status[req]['size_trasnferred'][t+1] = req_status[req]['size_trasnferred'][t]  + trasnfer_pertick1
                                req_status[req]['adto'] = t + time_taken1
                                
                                
                                
                                #update throughput_status accordingly
                                client_id = (clients_ip[requests_ip[req]['client']]['id'])
                                
                                
                                req_count1 = 1
                                #print("7 ",  str(t), throughput_status_time)
                                #del
                                req_count1 = 1
                                
                                if t+time_taken1 != throughput_status_time['temp_adto'][req]:
                                    #del throughput_status_time[client_id][throughput_status_time[client_id]['temp_adto']]
                                    del throughput_status_time[client_id][throughput_status_time['temp_adto'][req]]
                                    #throughput_status_time[client_id][throughput_status_time[client_id]['temp_adto']] -= 1
                                    if t+time_taken1 not  in throughput_status_time[client_id]:
                                        for key in throughput_status_time[client_id]:
                                            if key != 'old' and  key != 'temp_adto' :
                                                req_count1 += throughput_status_time[client_id][key]
                                        throughput_status_time[client_id][t + time_taken1] = req_count1
                                    else:
                                        throughput_status_time[client_id][t + time_taken1] += req_count1
                                        
                                    
                                    
                                    #throughput_status_time[client_id]['old'] = t+time_taken1
                                    
                                    
                                    throughput_status_time['temp_adto'][req] = t+time_taken1
                                #print("8", str(t),throughput_status_time)
                                #if throughput_status_time[client_id]['old'] == throughput_status_time[client_id]['temp_adto']:
                                     #throughput_status_time[client_id]['old'] = t + time_taken1
                                    
                                
                                #throughput_status_time[client_id]['temp_adto'] = t + time_taken1
                                
                                '''
                                #if throughput_status_time[client_id]['temp_adto'] != t+time_taken1  :
                                if  t+time_taken1 not in throughput_status_time[client_id] :                                       
                                        
                                        #throughput_status_time[client_id][throughput_status_time[client_id]['temp_adto']] -=1
                                        for key in throughput_status_time[client_id]:
                                            if key != 'old' and  key != 'temp_adto' and key < throughput_status_time[client_id][throughput_status_time[client_id]['temp_adto']] :                                            
                                                if throughput_status_time[client_id][key] > 1:
                                                    throughput_status_time[client_id][key] -=1
                                                else:
                                                    throughput_status_time[client_id][key] = 0
                                                    
                                                
                                        #throughput_status_time[client_id][throughput_status_time[client_id]['temp_adto']] -= 1
                                        print("7.1 ,",str(t),throughput_status_time)
                                        for key in throughput_status_time[client_id]:
                                            if key != 'old' and  key != 'temp_adto' and key != throughput_status_time[client_id]['temp_adto'] :
                                                req_count1 += throughput_status_time[client_id][key]
                                        
                                        throughput_status_time[client_id][t + time_taken1] = req_count1
                                        
                                        #if throughput_status_time[client_id]['old'] == throughput_status_time[client_id]['temp_adto']:
                                             #throughput_status_time[client_id]['old'] = t + time_taken1
                                            
                                        
                                        throughput_status_time[client_id]['temp_adto'] = t + time_taken1
                                
                                #throughput_status_time[client_id]['temp_adto'] = t + time_taken1
                                '''
                                req_status[req][t] = 'Storing asset in Cache'
                                
                                continue
                            elif t == req_status[req]['adto']:
                                req_status[req][t] = 'Asset transferred to cache server'
                                sim_status['connections_origin'][requests_ip[req]['origin']] -=1
                                sim_status['outbound_connections_cacheServer'] -=1
                                cacheServer_status['cacheserver1']['active_outbound_connections'] -= 1
                                #add asset to cache
                                cacheServer_ip['cacheserver1']['cached_assets_id'].append(requests_ip[req]['asset'])
                                req_status[req]['input_throughput_being_used']['cacheServer'] = 0
                                req_status[req]['output_throughput_being_used']['origin'] = 0
                                
                                cacheServer_id = requests_ip[req]['server']
                        #del throughput_status_time[client_id][req_status[req]['cct']]
                                for key in throughput_status_time[cacheServer_id]:
                                    if key != 'old':
                                        throughput_status_time[cacheServer_id][key] -=1
                                
                
                                
                                req_asset_id = requests_ip[req]['asset']
                                asset_size = int(assets_ip[req_asset_id]['size'])
                                cache_throughput = int(cacheServer_ip['cacheserver1']['max_output_throughput'])
                                client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                                #check available throughput-- 
                                available_throughput = min(cache_throughput,client_throughput)
                                time_taken = utility.timeToTransfer(asset_size,available_throughput)
                                req_status[req]['adtc1'] = t + time_taken
                                req_status[req]['stage'] = 5      
                                req_status[req]['size_trasnferred_toClient'] = {}
                                req_status[req]['size_trasnferred_toClient'][t] = 0
                        #handle adtc
                    if req_status[req]['stage'] ==  5:
                        if t < req_status[req]['adtc1']:
                                                           
                            client_id = (clients_ip[requests_ip[req]['client']]['id'])
                            req_asset_id = requests_ip[req]['asset']
                            asset_size = int(assets_ip[req_asset_id]['size'])  - req_status[req]['size_trasnferred_toClient'].get(t,0)
                            cache_throughput = int(cacheServer_ip['cacheserver1']['max_output_throughput'])
                            client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                                #check available throughput-- 
                            available_throughput = min(cache_throughput,client_throughput)
                            #n = throughput_status_time[client_id].get(t,0) + 1
                            #print(throughput_status_time)
                            
                            
                            #print(t, throughput_status_time[client_id]['old'])
                            te = throughput_status_time[client_id]['old']
                            if t in throughput_status_time[client_id]:
                                n = throughput_status_time[client_id].get(t)
                                throughput_status_time[client_id]['old'] = t
                                
                            else:
                                n = throughput_status_time[client_id][te]
                                
                            #n = throughput_status_time[client_id].get(t,1)
                            throughput_to_use = available_throughput/n
                            
                            req_status[req]['input_throughput_being_used']['client'] = throughput_to_use
                            req_status[req]['output_throughput_being_used']['cacheServer'] = throughput_to_use
                            cacheServer_status['cacheserver1']['output_throughput_available'] = int(cacheServer_ip['cacheserver1']['max_output_throughput']) - throughput_to_use
   
                            
                            time_taken = utility.timeToTransfer(asset_size,throughput_to_use)
                            trasnfer_pertick = asset_size / time_taken
                            #print(throughput_to_use, trasnfer_pertick, req, t)
                            #req_status[req]['size_trasnferred'][t+1] = (t+1 - req_status[req]['adto']) * trasnfer_pertick
                            req_status[req]['size_trasnferred_toClient'][t+1] = req_status[req]['size_trasnferred_toClient'][t]  + trasnfer_pertick
                            #print(req_status[req]['size_trasnferred_toClient'][t])
                            req_status[req]['adtc1'] = t + time_taken 
                            
                            req_status[req][t] = 'Transferring asset to client'
                            continue
                        elif t == req_status[req]['adtc1']:
                            req_status[req][t] = 'Asset transferred to client'
            
                            sim_status['inbound_connections_cacheServer'] -=1
                            cacheServer_status['cacheserver1']['active_inbound_connections'] -= 1
                            sim_status['connections_client'][requests_ip[req]['client']] -= 1
                            client_id = (clients_ip[requests_ip[req]['client']]['id'])  
                            #del throughput_status_time[client_id][req_status[req]['adto']]
                            for key in throughput_status_time[client_id]:
                                if key != 'old' and key != 'temp_adto' :
                                    if throughput_status_time[client_id][key] > 1:
                                        throughput_status_time[client_id][key] -=1
                                    else:
                                        throughput_status_time[client_id][key] = 0
                                    
                            req_status[req]['completed'] = 1
                            req_status[req]['input_throughput_being_used']['client'] = 0
                            req_status[req]['input_throughput_being_used']['cacheServer'] = 0
                            req_status[req]['output_throughput_being_used']['origin'] = 0
                            req_status[req]['output_throughput_being_used']['cacheServer'] = 0
                            
                total_cs_throughput_use=0
                for i in req_status.keys():
                    total_cs_throughput_use+=int(req_status[i]['input_throughput_being_used']['cacheServer'])
                cacheServer_status['cacheserver1']['input_throughput_used'] = total_cs_throughput_use
                if cacheServer_status['cacheserver1']['input_throughput_used'] == 0:
                    cacheServer_status['cacheserver1']['input_throughput_available']=int(cacheServer_ip["cacheserver1"]["max_input_throughput"])
                total_cs_throughput_use=0
                for i in req_status.keys():
                    total_cs_throughput_use+=int(req_status[i]['output_throughput_being_used']['cacheServer'])
                cacheServer_status['cacheserver1']['output_throughput_used'] = total_cs_throughput_use
                if cacheServer_status['cacheserver1']['output_throughput_used'] == 0:
                    cacheServer_status['cacheserver1']['output_throughput_available']=int(cacheServer_ip["cacheserver1"]["max_output_throughput"])


active_inbound_list=[]
active_outbound_list=[]
cacheserver_inputthroughput_list=[]
cacheserver_outputthroughput_list=[]
cacheserver_inputthroughputavailable_list=[]
tick_intervals=[] 
cache_hit=[]
cache_miss = []
cacheserver_outputthroughputavailable_list = []
request_list = []
workload_id={}

#def showing_plot(fig):
#    fig.show() 
def timer(requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip,workloads):
    dir = 'output'
    if not os.path.exists(dir):
        os.makedirs(dir)
    for workload in workloads.keys():
        dir='output/'+workload
        if not os.path.exists(dir)  :
            os.makedirs('output/'+workload)
        dir1='output/'+workload+'/visualization' 
        if not os.path.exists(dir1):
            os.makedirs('output/'+workload+'/visualization')
        dir2='output/'+workload+'/system_state'
        if not os.path.exists(dir2):
            os.makedirs('output/'+workload+'/system_state')

    
     
    line1 = []
    line2 = []
    line3 = [] 
    line4 = []
    line5 = []
    line6 = [] 
    line7 = []
    line8 = []
    line9 = []
    

    for t in range(simulation_ip['simulation1']['simulation_duration']+1): 

        simulation(t,requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip)
        #print(workload)
       
        if t%int(simulation_ip['simulation1']['tick_duration'])==0:            
            sim_stat=CaptureSystemState(t,simulation_ip,workload_ip,req_status,cacheServer_status,workloads)

            with open(os.path.join('output', workload, 'system_state', '%s.txt' %t), 'w') as outfile:                          
                json.dump(sim_stat, outfile, indent = 4)
                
        
        
        active_inbound_list.append(cacheServer_status['cacheserver1']['active_inbound_connections'])
        active_outbound_list.append(cacheServer_status['cacheserver1']['active_outbound_connections'])
        cacheserver_inputthroughput_list.append(cacheServer_status['cacheserver1']['input_throughput_used'])
        cacheserver_outputthroughput_list.append(cacheServer_status['cacheserver1']['output_throughput_used'])
        cacheserver_inputthroughputavailable_list.append(cacheServer_status['cacheserver1']['input_throughput_available'])
        cacheserver_outputthroughputavailable_list.append(cacheServer_status['cacheserver1']['output_throughput_available'])
        cache_hit.append(cacheServer_status['cacheserver1']['cache_hit'])
        cache_miss.append(cacheServer_status['cacheserver1']['cache_miss'])
        tick_intervals.append(t)
              
        count = 0
        for req in req_status.keys():
            if(req_status[req]['completed'] != 1):
                count=count+1
        request_list.append(count)
        
        request_count=0
        for i in workload_ip:
            request_count +=len(workload_ip[i])
        #print(request_count)
        
        #dynamic plots
        line1=live_plotter(tick_intervals,active_inbound_list,line1,'Time t','Active_inbound_connections','Time t vs Inbound Connections of Cache Server', simulation_ip['simulation1']['simulation_duration'],cacheServer_ip['cacheserver1']['max_connections']+1 )
#        line2=live_plotter(tick_intervals,active_outbound_list, line2,'Time t','Active_outbound_connections','Time t vs Outbound Connections of Cache Server',simulation_ip['simulation1']['simulation_duration'],cacheServer_ip['cacheserver1']['max_connections']+1)
#        line3=live_plotter(tick_intervals,cacheserver_inputthroughput_list, line3, 'Time t','Input_Throughput_used','Time t vs Input_Throughput_used (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_input_throughput'])+100)
#        line4=live_plotter(tick_intervals,cacheserver_outputthroughput_list, line4,'Time t','Output_Throughput_used','Time t vs Output_Throughput_used (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_output_throughput'])+100)
#        line5=live_plotter(tick_intervals, cacheserver_inputthroughputavailable_list, line5,'Time t','Output_Throughput_used','Time t vs Input_Throughput_Available (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_input_throughput'])+100)
#        line6=live_plotter(tick_intervals, cacheserver_outputthroughputavailable_list, line6,'Time t','Output_Throughput_used','Time t vs Output_Throughput_Available (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_output_throughput'])+100)
#        line7=live_plotter(tick_intervals, cache_hit, line7, 'Time t','Cache hit','Time t vs Cache hit',simulation_ip['simulation1']['simulation_duration'], request_count)
#        line8=live_plotter(tick_intervals, cache_miss, line8, 'Time t','Cache miss','Time t vs Cache miss',simulation_ip['simulation1']['simulation_duration'], request_count)
#        line9=live_plotter(tick_intervals,request_list, line9, 'Time t','Active_requests','Time t vs Active_Requests',simulation_ip['simulation1']['simulation_duration'], request_count)
#        a=t%int(simulation_ip['simulation1']['tick_duration'])
#        print(t,a)
        t +=1
    #static plots 
          
    def visualize(x,y,z,xlabel,ylabel,title,xlim,ylim,label1=None,label2=None):
        style.use('ggplot')
        ax = plt.figure().gca()
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        ax.set_xlim(0, xlim)
        ax.set_ylim(0, ylim)
              
        if z:
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))         
#            ax.plot(x,y,label=label1)
#            ax.plot(x,z,label=label2)
            ax.plot(x,y,'-o',alpha=0.8,label=label1)
            ax.plot(x,z,'-o',alpha=0.8,label=label2)
            plt.legend()
            plt.savefig('output/'+workload+'/visualization/%s.png' %title)
            
        else:            
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))        
            ax.plot(x,y,'-o',alpha=0.8)
            plt.savefig('output/'+workload+'/visualization/%s.png' %title)
        
    visualize(tick_intervals,active_inbound_list, [], 'Time t','Active_inbound_connections','Time t vs Inbound Connections of Cache Server' ,simulation_ip['simulation1']['simulation_duration'],cacheServer_ip['cacheserver1']['max_connections']+1)
    visualize(tick_intervals,active_outbound_list, [],'Time t','Active_outbound_connections','Time t vs Outbound Connections of Cache Server',simulation_ip['simulation1']['simulation_duration'],cacheServer_ip['cacheserver1']['max_connections']+1)
    visualize(tick_intervals,cacheserver_inputthroughput_list, [], 'Time t','Input_Throughput_used','Time t vs Input_Throughput_used (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_input_throughput'])+100)
    visualize(tick_intervals,cacheserver_outputthroughput_list, [],'Time t','Output_Throughput_used','Time t vs Output_Throughput_used (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_output_throughput'])+100)
    visualize(tick_intervals, cacheserver_inputthroughputavailable_list, [],'Time t','Output_Throughput_used','Time t vs Input_Throughput_Available (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_input_throughput'])+100)
    visualize(tick_intervals, cacheserver_outputthroughputavailable_list, [],'Time t','Output_Throughput_used','Time t vs Output_Throughput_Available (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip['cacheserver1']['max_input_throughput'])+100)
    visualize(tick_intervals,cache_miss, cache_hit, 'Time t','Cache hit/miss','Time t vs Cache hit & miss',simulation_ip['simulation1']['simulation_duration'], request_count,'cache_miss','cache_hit')
   # visualize(tick_intervals,cache_hit, [], 'Time t','Cache hit/miss','Time t vs Cache hit & miss','cache_miss','cache_hit',simulation_ip['simulation1']['simulation_duration'], 10)
    visualize(tick_intervals,request_list, [], 'Time t','Active_requests','Time t vs Active_Requests',simulation_ip['simulation1']['simulation_duration'], request_count)

    
    
def CaptureSystemState(snapshot_time,simulation_ip,workload_ip,req_status,cacheServer_status,workloads):  
    simulation_output={}
    simulation_output['tick_duration']=int(simulation_ip['simulation1']['tick_duration'])
    simulation_output['snapshot_time']=snapshot_time
    workload_id=list(workloads.keys())
    simulation_output['workload']=workload_id[0]

    
    simulation_output['requests_status']={}
    for req in req_status.keys():
        req_status_dict={}
        req_status_dict["initiated_at"]=req_status[req]['initiated_at']
        req_status_dict["client"]=req_status[req]["client"]
        req_status_dict["cacheServer"]="cacheServer1"
        req_status_dict["origin"]=req_status[req]["origin"]
        req_status_dict["asset"]=req_status[req]["asset"]
        req_status_dict["status"]=req_status[req].get(snapshot_time,"Request already processed")
        req_status_dict["input_throughput_being_used"]=req_status[req]['input_throughput_being_used']
        req_status_dict["output_throughput_being_used"]=req_status[req]['output_throughput_being_used']
        if req_status[req]['completed']==0: 
            req_status_dict["completed"]="No"
        else:
            req_status_dict["completed"]="Yes"
        simulation_output['requests_status'][req]=req_status_dict
        
    simulation_output['cacheserver_status']={}
    for cacheserver in cacheServer_status.keys():
        cs_status_dict={}
        cs_status_dict["cache_hit"]=cacheServer_status[cacheserver]["cache_hit"]
        cs_status_dict["cache_miss"]=cacheServer_status[cacheserver]["cache_miss"]
        cs_status_dict["input_throughput_being_used"]=cacheServer_status[cacheserver]["input_throughput_used"]
        cs_status_dict["output_throughput_being_used"]=cacheServer_status[cacheserver]["output_throughput_used"]
        cs_status_dict["input_throughput_available"]=cacheServer_status[cacheserver]["input_throughput_available"]
        cs_status_dict["output_throughput_available"]=cacheServer_status[cacheserver]["output_throughput_available"]
        cs_status_dict["number_of_active_inbound_connections"]=cacheServer_status[cacheserver]["active_inbound_connections"]
        cs_status_dict["number_of_active_outbound_connections"]=cacheServer_status[cacheserver]["active_outbound_connections"]
        simulation_output['cacheserver_status'][cacheserver]=cs_status_dict
        
    return simulation_output

def main():
    #os.chdir('C:/Users/Madhu/Desktop/Limelight-CDN-Model/input')
    f = open('input/'+sys.argv[1])
    contents = f.read()
    lines = contents.splitlines()

    simulation_ip = utility.read_json('input/'+lines[0])
    requests_ip = utility.read_json('input/'+lines[1])
    cacheServer_ip = utility.read_json('input/'+lines[2])
    assets_ip = utility.read_json('input/'+lines[3])
    clients_ip = utility.read_json('input/'+lines[4])
    origin_ip = utility.read_json('input/'+lines[5])
  #  workload_ip=utility.input_workload('input/'+lines[6])['workload2']
    workloads = utility.read_json('input/'+lines[6])
    workload_id=list(workloads.keys())
   # workload_id.append(workload_id1)
    workload_ip=utility.input_workload('input/'+lines[6])[workload_id[0]]

    
    
    #inputs=[simulation_ip,requests_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip,workload_ip]
    #collections=["simulation_input","requests","cacheservers","assets","clients","origins","workloads"]
    #utility.storeInputObjectsInDB(collections,inputs,utility.db)

    cacheServer_status['cacheserver1']['cache_hit'] = 0
    cacheServer_status['cacheserver1']['cache_miss'] = 0
    cacheServer_status['cacheserver1']['active_inbound_connections'] = 0
    cacheServer_status['cacheserver1']['active_outbound_connections'] = 0
    cacheServer_status['cacheserver1']['input_throughput_used'] = 0
    cacheServer_status['cacheserver1']['output_throughput_used'] = 0
    cacheServer_status['cacheserver1']['input_throughput_available'] = int(cacheServer_ip["cacheserver1"]["max_input_throughput"])
    cacheServer_status['cacheserver1']['output_throughput_available'] = int(cacheServer_ip["cacheserver1"]["max_output_throughput"])
    sim_status['inbound_connections_cacheServer'] = 0
    sim_status['outbound_connections_cacheServer'] = 0  
    sim_status['connections_client']={}
    sim_status['connections_origin']={}
    for req in requests_ip.keys():
        if req!="_id":
            client=requests_ip[req]['client']
            sim_status['connections_client'][client] = 0
            #sim_status['Client_throughput'][client] = 0
            origin=requests_ip[req]['origin']
            sim_status['connections_origin'][origin] = 0
            #sim_status['Origin_throughput'][origin] = 0
    timer(requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip,workloads)
   

    
if __name__ == '__main__':
    main()
#    
#pprint(req_status)
#pprint(cacheServer_status)   
#pprint(sim_status)



    
