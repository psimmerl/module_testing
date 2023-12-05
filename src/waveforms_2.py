"""waveforms

functions for acquiring and processing waveforms.


Scan over-voltages and trigger thresholds for a module.
1. Use wavedump (or acquire-waveforms?) to collect over-voltage and trigger threshold data for a chosen source type
    -   Save each waveform's integrated charge, if it's saturated, t_{10%}, t_{90%}, and anything else?
2. Analysis of integrated wave

"""
import os
import sys
import argparse

import numpy as np

# import scipy as sp

import ROOT as rt

#import relevant modules from analyze-waveforms
from qaqc_jig.python.analyze-waveforms import integrate, get_window, get_spe_window, spe_baseline_subtraction, convert_data, get_threshold_crossing, chunks, get_rise_time, get_fall_time, SOURCES

def acquire_waveforms(waveform_path, n_events, l: str = "sodium", ov: float = 2.2, thresholds: float = -0.05, **kwargs):
    """wavedump -t self -l sodium --channel-map 1 -n"""

    """acquire_waveforms
    Acquire waveforms from the QAQC jig and saves to an hdf5 file.
    """

    return


def process_waveforms(waveform_path: str, root_path: str, **kwargs):
    """process_waveforms
    Process a waveform file (hdf5) from the QAQC jig and save the reduced file as a ROOT nTuple. Can later be loaded into an RDataframe for more advanced analyses. Returns the nTuple

    params:
    waveform_path   str
        path of the hdf5 file where the waveforms are saved
    root_path    str
        path of the root file where the processed waveforms' data is saved
    branches    str, iterable
        choose what data is saved to your proc

    return [ ( trigger channel, trigger time, { channel ID, charge, t 10%, t 90%, saturation ; for the 8 channels in the trigger group } ) ; for N_EVENTS in each of the 4 trigger groups ]
    """
    
    if not args.plot:
        # Disables the canvas from ever popping up
        gROOT.SetBatch()


    data = {}
    ch_data = {}  
    if args.upload:
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
    with h5py.File(args.filename,'r') as f:
        if len(SOURCES.keys() & set(f)) > 1:
            print('Can not analyze file with more than one source!', file=sys.stderr)
            sys.exit(1)
        if len(SOURCES.keys() & set(f)) == 1:
            source = list(SOURCES.keys() & set(f))[0]
        # If there is no source in the data set, then we can still analyze SPE
        # data.

        root_f = ROOT.TFile(args.output, "recreate")
                
        if args.upload:
            if args.upload:
            # Database is only built for LYSO data
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

            if 'barcode' in f['lyso'].attrs:
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
        
        for group in f:
            
            if args.group is not None and group != args.group:
                continue
            
            if group not in SOURCES and group != 'spe':
                print("Unknown group name: \"%s\". Skipping..." % group)
                continue

            
            #define NTuple for given trigger group
            tree = ROOT.TTree("Group " + str(group), "NTuples for Trigger Group " + str(group))

            for channel in f[group]:
                # All relevant channels from the scope and digitizer should
                # be in this format: 'ch<channel number>'.
                if not channel.startswith('ch'):
                    continue

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

                #add lists for t 10%, t 90%, and saturation (boolean list)
                
                t10 = []; t90 = []; saturation = []

                ##################
                # Integrations
                ##################
                print(f'Integrating {group} {channel}...')
                for i in range(0, len(f[group][channel]), args.chunks):
                    x, y = convert_data(f, group, channel, i, i+args.chunks)
                    if group == source:
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
                        
                    elif group == 'spe':
                        a, b = get_spe_window(x, args.start_time, args.integration_time)
                        y = spe_baseline_subtraction(x, y, a, b, method=args.integration_method)

                    charge.extend(integrate(x,y, a, b))
                    t10.extend(get_threshold_crossing(x, y, 0.1))
                    t90.extend(get_threshold_crossing(x, y, 0.9))
                    #determine if saturated - will modify later
                    sat = False
                    ### Determine if given channel saturates for given event
                    saturation.extend(sat)

                #ch_data[channel]['%s_charge' % group] = np.array(charge)

                #add event-by-event integrated charge for specific channel as a branch of the TTree for this trigger group
                #tree.Branch("Integrated_Charge_Ch_" + str(channel), ch_data[channel]['%s_charge' % group], "Integrated_Charge_Ch_" + str(channel)[{len(ch_data[channel]['%s_charge' % group])}/D]")
                BranchNameCharge = "Integrate_Charge_Ch" + str(channel)
                tree.branch(BranchNameCharge, np.array(charge), BranchNameCharge/D)
                
                #same for times
                BranchNamet10 = "t10_" + str(channel); BranchNamet90 = "t90_" + str(channel); BranchNameSat = "Saturation_" + str(channel)
                tree.branch(BranchNamet10, np.array(t10), BranchNamet10/D)
                tree.branch(BranchNamet90, np.array(t90), BranchNamet90/D)
                tree.branch(BranchNameSat, np.array(saturation, dtype=np.bool_), BranchNameSat/0)
                


                #fill tree with branch and write to file
                tree.Fill()
                root_f.Write()






    return





if __name__ == "__main__":
    overvoltages = []

    pass

    #this code is replicated directly from the analyze-waveforms file. It consists of sections INTEGRATIONS, CREATING HISTOGRAM
    # PREPARING DATA FOR UPLOAD, FITTING HISTOGRAM, REVIEWING DATA, and UPLOADING DATA
    # I only keep INTEGRATIONS and the code for determining threshold times - storing data will be different as we are using nTuples
    
    
    from argparse import ArgumentParser
    import ROOT
    from ROOT import gROOT
    import matplotlib.pyplot as plt
    import psycopg2
    import psycopg2.extensions
    from btl import fit_spe_funcs
    from btl import fit_lyso_funcs



    parser = ArgumentParser(description='Analyze SPE and LYSO charges')
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
    args = parser.parse_args()

    #pass these args to process_waveforms





                
                        
