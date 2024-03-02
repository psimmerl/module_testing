"""waveforms

functions for acquiring and processing waveforms.


Scan over-voltages and trigger thresholds for a module.
1. Use wavedump (or acquire-waveforms?) to collect over-voltage and trigger threshold data for a chosen source type
    -   Save each waveform's integrated charge, if it's saturated, t_{10%}, t_{90%}, and the channel in the group that triggered the event?
2. Analysis of integrated wave

"""
#import statements
import os
import sys
import argparse

import numpy as np
import pandas as pd
# import scipy as sp

#set PYTHONPATH so we can import the needed modules from Tony's 'analyze_waveforms.py' script
sys.path.insert(0, '/home/cptlab/dt5742/python')
from analyze_waveforms import *

import ROOT

def acquire_waveforms(waveform_path, n_events, l: str = "sodium", ov: float = 2.2, thresholds: float = -0.05, **kwargs):
    """
    code to acquire waveforms from either existing wavedump or acquire_waveforms scripts. Important parameters
    are SOURCE, OVERVOLTAGE, and TRIGGER THRESHOLD.
    
    wavedump -t self -l sodium --channel-map 1 -n"""

    """acquire_waveforms
    Acquire waveforms from the QAQC jig and saves to an hdf5 file.
    """

    return


def checkSat(waveforms_array): 
    #helper function: input waveform-level information and output bool Array for event saturation
    minVals = np.amin(waveforms_array.T, axis=0)
    return np.array([minVals==0.0][0], dtype=np.int_)
    

#def process_waveforms(waveform_path: str, root_path: str, **kwargs):
def process_waveforms(args, **kwargs):
    """process_waveforms
    Process a waveform file (hdf5) from the QAQC jig and save the reduced file as an RDataFrame

    params:
    waveform_path   str
        path of the hdf5 file where the waveforms are saved
    root_path    str
        path of the root file where the processed waveforms' data is saved
    boolean flags:
        -c: compute times to 10%, 90% of total waveform intensity on intitial voltage decrease
        -m: if True, will merge RDataFrames from each trigger group into a single RDataFrame (still different RDataframes for both sources
        --compute_saturation: if True, RDataFrame will include a bool/int valued branch that denotes if a given event saturated that channel

    return [ ( trigger channel, trigger time, { channel ID, charge, t 10%, t 90%, saturation ; for the 8 channels in the trigger group } ) ; for N_EVENTS in each of the 4 trigger groups ]
    """

    if not args.plot:
        # Disables the canvas from ever popping up
        gROOT.SetBatch()

    data = {}
    ch_data = {}  
    if args.upload: #upload stuff from Tony
        if 'BTL_DB_HOST' not in os.environ:
            print("need to set BTL_DB_HOST environment variable!",file=sys.stderr)
            sys.exit(1)

        if 'BTL_DB_PASS' not in os.environ:
            print("need to set BTL_DB_PASS environment variable!",file=sys.stderr)
            sys.exit(1)

        print("Making upload connection to the database...")
        conn = psycopg2.connect(dbname='btl_qa',
                                user='btl',
                                host=os.environ['BTL_DB_HOST'],
                                password=os.environ['BTL_DB_PASS'])
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()

    data = {}
    ch_data = {}
    print("Input File = " + args.filename)
    with h5py.File(args.filename,'r') as f: #open input file, check what the source is
        if len(SOURCES.keys() & set(f)) > 1:
            print('Can not analyze file with more than one source!', file=sys.stderr)
            sys.exit(1)
        if len(SOURCES.keys() & set(f)) == 1:
            source = list(SOURCES.keys() & set(f))[0]
        # If there is no source in the data set, then we can still analyze SPE
        # data.
        print("Source:" ,source)
        root_f = ROOT.TFile(args.output, "recreate")
                
        if args.upload:
            if source != 'lyso':
                print("Missing lyso data!", file=sys.stderr)
                sys.exit(1)
            if 'spe' not in dict(f):
                print("Missing SPE data!", file=sys.stderr)
                sys.exit(1)
            
            #for param in f['lyso'].attrs:
            #    if f['lyso'].attrs[param] != f['spe'].attrs[param]:
            #        print("Conflict in %s used to take lyso and SPE data!" % param, file=sys.stderr)
            #        sys.exit(1)
            if 'data_source' in f['lyso'].attrs:
                if f['lyso'].attrs['data_source'] != b'CAEN':
                    print("Error: trying to upload non-CAEN data!", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Data source not specified!", file=sys.stderr)
                sys.exit(1)
            
            data['git_sha1'] = f['lyso'].attrs['git_sha1'].decode("UTF-8")
            data['git_dirty'] = f['lyso'].attrs['git_dirty'].decode("UTF-8")
            if 'institution' in f.attrs:
                data['institution'] = f.attrs['institution']
            elif args.institution is not None:
                data['institution'] = str(args.institution)
            else:
                print("Error: no institution specified in hdf5 file or with -i option!",file=sys.stderr)
                sys.exit(1)

            data['filename'] = args.filename

            if 'barcode' in f['lyso'].attrs: #barcode stuff from Tony
                # Here for backwards compatibility with data taken at Fermilab
                data['barcode'] = int(f['lyso'].attrs['barcode'])
                data['voltage'] = float(f['lsyo'].attrs['voltage'])
            else:
                data['barcode'] = int(f.attrs['barcode'])
                data['voltage'] = float(f.attrs['voltage'])

            try:
                data['tec_a'] = f.attrs['tec_a']
                data['tec_b'] = f.attrs['tec_b']
                data['temp_a'] = f.attrs['temp_a']
                data['temp_b'] = f.attrs['temp_b']
            except KeyError as e:
                data['tec_a'] = None
                data['tec_b'] = None
                data['temp_a'] = None
                data['temp_b'] = None

            cursor.execute("INSERT INTO runs (voltage, institution, git_sha1, git_dirty, filename, tec_resistance_a, tec_resistance_b, temp_a, temp_b) VALUES (%(voltage)s, %(institution)s::inst, %(git_sha1)s, %(git_dirty)s, %(filename)s, %(tec_a)s, %(tec_b)s, %(temp_a)s, %(temp_b)s) RETURNING run", data)
            result = cursor.fetchone()
            run = result[0]
        
        listTriggerGroups = [(0,7),(8,15),(16,23),(24,31)] #Starting and ending trigger channels for each group
        '''
            The output data file will be organized into 4 RDataFrames. 
            1. Radioactive Source Data + Trigger Group 1
            2. Radioactive Source Data + Trigger Group 2
            3. Radioactive Source Data + Trigger Group 3
            4. Radioactive Source Data + Trigger Group 4
            5. SPE + Trigger Group 1
            6. SPE + Trigger Group 2
            7. SPE + Trigger Group 3
            8. SPE + Trigger Group 4
        '''
        
        
        for groupNum, group in enumerate(f): #iterate over source+spe
            
            if args.group is not None and group != args.group:
                continue
            
            if group not in SOURCES and group != 'spe':
                print("Unknown group name: \"%s\". Skipping..." % group)
                continue
            
            minLens=  []; triggerGroup_DictList=  [] #only important if merging RDataFrames
            for triggerGroup, channelTuple in enumerate(listTriggerGroups):
                Group_Source_Dict = {}
                integratedChargeChannels= []; t10Channels=[]; t90Channels=[]; saturationChannels=[]
                for channelNum in range(channelTuple[0],channelTuple[1]+1):
                    #for channel in f[group]:
                    # All relevant channels from the scope and digitizer should
                    # be in this format: 'ch<channel number>'.
                    #if not channel.startswith('ch'):
                    #    continue
                    channel = "ch"+str(channelNum)
                    ch = int(channel[2:])

                    if not args.channel_mask & (1 << ch):
                        continue
                    
                    # Only active channel is analyzed, unless it's `None`, in
                    # which case all channels are analyzed.
                    if args.active and channel != args.active:
                        continue
                    
                    if channel not in ch_data:
                        ch_data[channel] = {'channel': int(channel[2:])}
                    
                    if args.upload:
                        ch_data[channel]['run'] = run
                        ch_data[channel]['barcode'] = data['barcode']
                     
                    charge = []

                    #add lists for t 10%, t 90%, and saturation
                    
                    t10 = []; t90 = []; saturation = []

                    ##################
                    # Integrations
                    ##################
                    #print(f'Integrating {group} {channel}...')
                    for i in range(0, len(f[group][channel]), args.chunks):
                        x, y = convert_data(f, group, channel, i, i+args.chunks) #store group/channel waveform info as large numpy array
                        if group == source and args.saturation_flag: #note that we do check saturation before doing any baseline subtraction
                            saturation.extend(checkSat(y))
                        if group == source: #find relevant waveform points for source events
                            a, b = get_window(x,y, left=50, right=350)
                            y -= np.median(y[:,x < x[0] + 100],axis=-1)[:,np.newaxis]
                            if 'avg_pulse_y' in ch_data[channel]:
                                ch_data[channel]['avg_pulse_y'] = (ch_data[channel]['avg_pulse_count']*ch_data[channel]['avg_pulse_y'] + len(y)*np.mean(y, axis=0)) / (ch_data[channel]['avg_pulse_count'] + len(y))
                                ch_data[channel]['avg_pulse_count'] += len(y)
                                np.append(ch_data[channel][f'{group}_rise_time'], get_rise_time(x, y))
                                np.append(ch_data[channel][f'{group}_fall_time'], get_fall_time(x, y))
                            else:
                                ch_data[channel]['avg_pulse_y'] = np.mean(y, axis=0)
                                ch_data[channel]['avg_pulse_count'] = len(y)
                                ch_data[channel]['avg_pulse_x'] = x
                                ch_data[channel][f'{group}_rise_time'] = get_rise_time(x, y)
                                ch_data[channel][f'{group}_fall_time'] = get_fall_time(x, y)
                            
                        elif group == 'spe': #find relevant waveform points at do baseline subtraction for spe
                            a, b = get_spe_window(x, args.start_time, args.integration_time)
                            y = spe_baseline_subtraction(x, y, a, b, method=args.integration_method)

                        charge.extend(integrate(x,y, a, b)) #load in integrated charge values
                        if args.compute_timing_info: #load in timing info if timing flag set to True
                            t10.extend(get_threshold_crossing(x, y, 0.1))
                            t90.extend(get_threshold_crossing(x, y, 0.9))


                    #Add charge, timing, etc info from each branch into an array with info for all channels
                    #this will be necessary to ensure all branches have the same length and allows us to compute  the triggering channel
                    npCharge = np.array(charge, dtype=np.float32)
                    integratedChargeChannels.append(npCharge)
                    if args.compute_timing_info:
                        t10Channels.append(np.array(t10, dtype=np.float32))
                        t90Channels.append((np.array(t90, dtype=np.float32)))
                    
                    if args.saturation_flag and group==source:
                        saturationChannels.append(np.array(saturation, dtype=np.int_))
                
                
                #determine which channel triggered on a given event
                #we do this by determing the channel that had the greatest integrated charge on an event-by-event basis
                
                #get length of shortest list in integratedChargeChannels
                #otherwise, there may be different number entries for each channel (mainly for SPEs)
                minLen = min([len(x) for x in integratedChargeChannels])
                minLens.append(minLen)
                #slice each integratedChargeArray and timing/saturation arrays so that they have the same length
                #this is usually only necessary for SPEs
                integratedChargeChannels = [chargeArray[0:minLen] for chargeArray in integratedChargeChannels]
                if args.compute_timing_info: 
                    t10Channels = [timeArray[0:minLen] for timeArray in t10Channels]
                    t90Channels = [timeArray[0:minLen] for timeArray in t90Channels]
                if args.saturation_flag and group==source:
                    saturationChannels = [satArray[0:minLen] for satArray in saturationChannels]
                integrationsNp = np.stack(integratedChargeChannels)

                triggerIndex = np.argmax(integrationsNp, axis=0)
                triggerChannel  = np.zeros(minLen, dtype=int)
                
                #iterate through channels to create dictionary with branches, as well as to determine triggering channel
                for index, channelNum in enumerate(range(channelTuple[0],channelTuple[1]+1)):
                    triggerLocs = np.where(triggerIndex==index)[0]
                    triggerChannel[triggerLocs]=np.short(channelNum)
                    Group_Source_Dict[f'ch{channelNum}_IntegratedCharge'] = integratedChargeChannels[index]
                    if args.compute_timing_info:
                        Group_Source_Dict[f'ch{channelNum}_t10'] = t10Channels[index]
                        Group_Source_Dict[f'ch{channelNum}_t90'] = t90Channels[index]
                    if args.saturation_flag and group==source:
                        Group_Source_Dict[f'ch{channelNum}_satFlag'] = saturationChannels[index]



                Group_Source_Dict["channelTriggered"] = triggerChannel
                
                #generate RDataFrames from dictionary, output to file IF not merging trigger group information
                if not args.merge_RDataFrames:
                    print("About to Write RDataFrame for Source" + str(group) + " Trigger Group " + str(triggerGroup+1))
                    df = ROOT.RDF.FromNumpy(Group_Source_Dict)
                    #df = ROOT.RDF(Group_Source_Dict)
                    print(f"{group}_TriggerGroup{triggerGroup+1}") 
                    opts = ROOT.RDF.RSnapshotOptions()
                    if groupNum !=0 or triggerGroup!=0:
                        opts.fMode = "update" #ensures file is in update mode when adding subsequent RDataframes
                    df.Snapshot(f"{group}_TriggerGroup{triggerGroup+1}", args.output, "", opts)
                
                else:
                    triggerGroup_DictList.append(Group_Source_Dict)

            if not args.merge_RDataFrames:
                continue
            else: #if merging, we need to combine the dictionary for each trigger group into a single one
                print("About to merge RDataFrames for", group)
                mergedDict = {}; dictLen = min(minLens) #ensure there are the same number of events from each trigger group
                for groupIndex, myDict in enumerate(triggerGroup_DictList):
                    zerosBefore = groupIndex; zerosAfter = 3 - groupIndex #add arrays of zeros corresponding to events from different trigger groups
                    for key, value in myDict.items():
                        mergedDict[key] = np.concatenate((np.zeros(dictLen*zerosBefore),value[:dictLen],np.zeros(dictLen*zerosAfter))) #add dictionary entry list with zeros for events from other trigger groups
                        #if "Trigger" in key:
                        #    mergedDict[f'channelTriggered_Group{groupIndex+1}'] = value[:dictLen]
                df = ROOT.RDF.FromNumpy(mergedDict)
                opts = ROOT.RDF.RSnapshotOptions()
                if groupNum!=0:
                    opts.fMode = "update"
                df.Snapshot(f'{group}_AllTriggerGroups', args.output,"", opts)


    return


if __name__ == "__main__":
    overvoltages = []

    pass

    from argparse import ArgumentParser
    import ROOT
    from ROOT import gROOT
    import matplotlib.pyplot as plt
    import psycopg2
    import psycopg2.extensions
    from btl import fit_spe_funcs
    from btl import fit_lyso_funcs


    #Most of these arguments are from 'analyze_waveforms'. 
    parser = ArgumentParser(description='Analyze SPE and Source charges')
    parser.add_argument('filename',help='input filename (hdf5 format)')
    parser.add_argument('-o','--output', default='delete_me.root', help='output file name')
    parser.add_argument('--plot', default=False, action='store_true', help='plot the waveforms and charge integral')
    parser.add_argument('--chunks', default=10000, type=int, help='number of waveforms to process at a time')
    parser.add_argument('-t', '--integration-time', default=150, type=float, help='SPE integration length in nanoseconds.')
    parser.add_argument('-s', '--start-time',  default=50, type=float, help='start time of the SPE integration in nanoseconds.')
    parser.add_argument('--active', default=None, help='Only take data from a single channel. If not specified, all channels are analyzed.')
    parser.add_argument('--integration-method', type=int, default=1, help='Select a method of integration. Methods described in __main__')
    parser.add_argument("--print-pdfs", default=None, type=str, help="Folder to save pdfs in.")
    parser.add_argument('-u','--upload', default=False, action='store_true', help='upload results to the database')
    parser.add_argument('-i','--institution', default=None, type=Institution, choices=list(Institution), help='name of institution')
    parser.add_argument('--channel-mask', type=lambda x: int(x,0), default=0xffffffff, help='channel mask')
    parser.add_argument('-g', '--group', type=str, default=None, help='which group to analyze')
    
    #bool flags added by Alex to specify info in output RDataFrames
    parser.add_argument('-c', '--compute_timing_info', action='store_true', help='flag to compute time to 10% and 90% total intensity on rising edge')
    parser.add_argument('-m', '--merge_RDataFrames', action='store_true', help='flag to merge dataframes from each trigger group into a single one')
    parser.add_argument('--saturation_flag', action='store_true', help='flag source events with saturated waveform')
    args = parser.parse_args()
    import analyze_waveforms
    analyze_waveforms.args=args 
    #pass these args to process_waveforms
    process_waveforms(args)




                
                        
