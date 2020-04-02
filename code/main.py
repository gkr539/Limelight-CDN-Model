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






import utility
import collections
from pprint import pprint


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
            #print(requests_ip[req])
            req_status[req] = {t : "started"}
            req_status[req]['initiated_at'] = t
            req_status[req]['tctc'] = t + int(simulation_ip['sim1']['tcp_connection_time'])
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
        for req in req_status.keys():
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
                        max_connections_cache = cacheServer_ip['cacheserver1']["max_connections"]
                        if (sim_status['inbound_connections_cacheServer'] < max_connections_cache) and (sim_status['connections_client'][requests_ip[req]['client']] < max_connections_client):
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
                                
                                    req_count = 1
                                    for key in throughput_status_time[client_id]:
                                        if key != 'old':
                                            req_count += throughput_status_time[client_id][key]
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
                            req_status[req]['tcto'] = t + int(simulation_ip['sim1']['tcp_connection_time'])
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
                            if key != 'old':
                                throughput_status_time[client_id][key] -=1
                                                
                        
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
                            if sim_status['connections_origin'][requests_ip[req]['origin']] < int(origin_ip[requests_ip[req]['origin']]["max_connections"]):
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
                                print(throughput_status_time)
                               
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
                                del throughput_status_time[client_id][throughput_status_time[client_id]['temp_adto']]
                                #throughput_status_time[client_id][throughput_status_time[client_id]['temp_adto']] -= 1
                                for key in throughput_status_time[client_id]:
                                    if key != 'old' and  key != 'temp_adto':
                                        req_count1 += throughput_status_time[client_id][key]
                                throughput_status_time[client_id][t + time_taken1] = req_count1
                                
                                #if throughput_status_time[client_id]['old'] == throughput_status_time[client_id]['temp_adto']:
                                     #throughput_status_time[client_id]['old'] = t + time_taken1
                                    
                                
                                throughput_status_time[client_id]['temp_adto'] = t + time_taken1
                                
                                #throughput_status_time[client_id]['temp_adto'] = t + time_taken1
                                req_status[req][t] = 'Storing asset in Cache'
                                continue
                            elif t == req_status[req]['adto']:
                                req_status[req][t] = 'Asset transferred to cache server'
                                sim_status['connections_origin'][requests_ip[req]['origin']] -=1
                                sim_status['outbound_connections_cacheServer'] -=1
                                cacheServer_status['cacheserver1']['active_outbound_connections'] -= 1
                                #add asset to cache
                                cacheServer_ip['cacheserver1']['cached_assets_id'].append(requests_ip[req]['asset'])
                                
                                
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
                                    throughput_status_time[client_id][key] -=1
                                    
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
                            
    

def timer(requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip): 
    for t in range(simulation_ip['sim1']['simulation_duration']):   
        simulation(t,requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip)
        if t%int(simulation_ip['sim1']['tick_duration'])==0:
            print("store system state in mongodb")
            sim_stat=CaptureSystemState(t,simulation_ip,workload_ip,req_status,cacheServer_status)
            utility.storeObjectInDB("systemstate",[sim_stat],utility.db)
        t +=1

    
def CaptureSystemState(snapshot_time,simulation_ip,workload_ip,req_status,cacheServer_status):  
    simulation_output={}
    simulation_output['tick_duration']=int(simulation_ip['sim1']['tick_duration'])
    simulation_output['snapshot_time']=snapshot_time
    simulation_output['workload']="workload1"
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
    simulation_ip = utility.read_json('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/Simulation.json')
    requests_ip = utility.read_json('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/requests.json')
    cacheServer_ip = utility.read_json('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/cacheserver.json')
    assets_ip = utility.read_json('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/asset.json')
    clients_ip = utility.read_json('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/clients.json')
    origin_ip = utility.read_json('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/origin.json')
    workload_ip=utility.read_json('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/Workload.json') 
    inputs=[simulation_ip,requests_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip,workload_ip]
    collections=["simulation_input","requests","cacheservers","assets","clients","origins","workloads"]
    utility.storeInputObjectsInDB(collections,inputs,utility.db)
    workload_ip=utility.input_workload('/Users/srikanth/Desktop/Courses/CSE611-MSProject/ip/Workload.json')['workload1']
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
            origin=requests_ip[req]['origin']
            sim_status['connections_origin'][origin] = 0
    timer(requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip)
   
    

if __name__ == '__main__':
    main()
    
pprint(req_status)
pprint(cacheServer_status)    
    
