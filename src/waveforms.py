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
from qaqc_jig.python.analyze-waveforms import integrate, get_window, get_spe_window, spe_baseline_subtraction, convert_data

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

    return





if __name__ == "__main__":
    overvoltages = []

    pass

    #this code is replicated directly from the analyze-waveforms file. It consists of sections INTEGRATIONS, CREATING HISTOGRAM
    # PREPARING DATA FOR UPLOAD, FITTING HISTOGRAM, REVIEWING DATA, and UPLOADING DATA
    # I only keep INTEGRATIONS, PREPARING DATA FOR UPLOAD, REVIEWING DATA, and UPLOADING DATA
    
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

    if not args.plot:
        # Disables the canvas from ever popping up
        gROOT.SetBatch()

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
        root_f = ROOT.TFile(args.output, "recreate")
                
        if args.upload:
            if 'lyso' not in dict(f):
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

            if group != 'lyso' and group != 'spe':
                print("Unknown group name: \"%s\". Skipping..." % group)
                continue

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
                
                ##################
                # Integrations
                ##################
                print(f'Integrating {group} {channel}...')
                for i in range(0, len(f[group][channel]), args.chunks):
                    x, y = convert_data(f, group, channel, i, i+args.chunks)
                    if group == 'lyso':
                        a, b = get_window(x,y, left=50, right=350)
                        y -= np.median(y[:,x < x[0] + 100],axis=-1)[:,np.newaxis]
                        if 'avg_pulse_y' in ch_data[channel]:
                            ch_data[channel]['avg_pulse_y'] = (ch_data[channel]['avg_pulse_count']*ch_data[channel]['avg_pulse_y'] + len(y)*np.mean(y, axis=0)) / (ch_data[channel]['avg_pulse_count'] + len(y))
                            ch_data[channel]['avg_pulse_count'] += len(y)
                            np.append(ch_data[channel]['lyso_rise_time'], get_rise_time(x, y))
                            np.append(ch_data[channel]['lyso_fall_time'], get_fall_time(x, y))
                        else:
                            ch_data[channel]['avg_pulse_y'] = np.mean(y, axis=0)
                            ch_data[channel]['avg_pulse_count'] = len(y)
                            ch_data[channel]['avg_pulse_x'] = x
                            ch_data[channel]['lyso_rise_time'] = get_rise_time(x, y)
                            ch_data[channel]['lyso_fall_time'] = get_fall_time(x, y)
                        
                    elif group == 'spe':
                        a, b = get_spe_window(x, args.start_time, args.integration_time)
                        y = spe_baseline_subtraction(x, y, a, b, method=args.integration_method)

                    charge.extend(integrate(x,y, a, b))

                ch_data[channel]['%s_charge' % group] = np.array(charge)



                ##################
                # Preparing Data for Upload
                ##################
                if args.upload:
                    if 'lyso_charge' in ch_data[channel]:
                        ch_data[channel]['lyso_rise_time'] = float(np.nanmedian(ch_data[channel]['lyso_rise_time']))
                        ch_data[channel]['lyso_fall_time'] = float(np.nanmedian(ch_data[channel]['lyso_rise_time']))
                        ch_data[channel]['avg_pulse_x'] = list(map(float,ch_data[channel]['avg_pulse_x']))
                        ch_data[channel]['avg_pulse_y'] = list(map(float,ch_data[channel]['avg_pulse_y']))
                        lyso_bincenters = (lyso_bins[1:] + lyso_bins[:-1])/2
                        ch_data[channel]['lyso_charge_histogram_y'] = list(map(float,np.histogram(ch_data[channel]['lyso_charge'][selection],bins=lyso_bins)[0]))
                        ch_data[channel]['lyso_charge_histogram_x'] = list(map(float,lyso_bincenters))
                    else:
                        ch_data[channel]['lyso_rise_time'] = None
                        ch_data[channel]['lyso_fall_time'] = None
                        ch_data[channel]['avg_pulse_x'] = None
                        ch_data[channel]['avg_pulse_y'] = None
                        ch_data[channel]['lyso_charge_histogram_y'] = None
                        ch_data[channel]['lyso_charge_histogram_x'] = None
                    if 'spe_charge' in ch_data[channel]:
                        spe_bincenters = (spe_bins[1:] + spe_bins[:-1])/2
                        ch_data[channel]['spe_charge_histogram_y'] = list(map(float,np.histogram(ch_data[channel]['spe_charge'],bins=spe_bins)[0]))
                        ch_data[channel]['spe_charge_histogram_x'] = list(map(float,spe_bincenters))
                    else:
                        ch_data[channel]['spe_charge_histogram_y'] = None
                        ch_data[channel]['spe_charge_histogram_x'] = None


                ##################
                # Reviewing Data
                ##################
                for channel in sorted(ch_data, key=lambda channel: int(channel[2:])):
                    if 'pc_per_kev' not in ch_data[channel]:
                        print('Mising lyso data for %s!' % channel)
                    elif 'spe' not in ch_data[channel]:
                        print('Missing SPE data for %s!' % channel)
                    elif ch_data[channel]['pc_per_kev'] is None:
                        print('Failed to fit %s lyso histogram!' % channel)
                    elif ch_data[channel]['spe'] is None:
                        print('Failed to fit %s spe histogram!' % channel)
                    else:
                        print('%s: %.2f' % (channel, ch_data[channel]["pc_per_kev"]*1000*ATTENUATION_F

                ##################
                # Uploading Data
                ##################
            if args.upload:
                result = cursor.execute("INSERT INTO data (channel, barcode, pc_per_kev, spe, lyso_rise_time, lyso_fall_time, lyso_charge_histogram_x, lyso_charge_histogram_y, spe_charge_histogram_x, spe_charge_histogram_y, avg_pulse_x, avg_pulse_y, run, spe_fit_pars, lyso_fit_pars, spe_fit_par_errors, lyso_fit_par_errors) VALUES (%(channel)s, %(barcode)s, %(pc_per_kev)s, %(spe)s, %(lyso_rise_time)s, %(lyso_fall_time)s, %(lyso_charge_histogram_x)s, %(lyso_charge_histogram_y)s, %(spe_charge_histogram_x)s, %(spe_charge_histogram_y)s, %(avg_pulse_x)s, %(avg_pulse_y)s, %(run)s, %(spe_fit_pars)s, %(lyso_fit_pars)s, %(spe_fit_par_errors)s, %(lyso_fit_par_errors)s)", ch_data[channel])

    x = array('d')
    y = array('d')
    pc_per_kev = array('d')
    pc_per_kev_err = array('d')
    spe = array('d')
    spe_err = array('d')
    yerr = array('d')
    for channel in sorted(ch_data, key=lambda channel: int(channel[2:])):
        if 'lyso_fit_pars' not in ch_data[channel]:
            continue
        if 'spe_fit_pars' not in ch_data[channel]:
            continue
        lyso_fit_pars = ch_data[channel]['lyso_fit_pars']
        spe_fit_pars = ch_data[channel]['spe_fit_pars']
        lyso_fit_par_errors = ch_data[channel]['lyso_fit_par_errors']
        spe_fit_par_errors = ch_data[channel]['spe_fit_par_errors']
        if lyso_fit_pars is not None and spe_fit_pars is not None:
            x.append(int(channel[2:]))
            y.append(lyso_fit_pars[0]*ATTENUATION_FACTOR*1000/spe_fit_pars[3])
            pc_per_kev.append(lyso_fit_pars[0])
            pc_per_kev_err.append(lyso_fit_par_errors[0])
            spe.append(spe_fit_pars[3])
            spe_err.append(spe_fit_par_errors[3])
            dlyso = lyso_fit_par_errors[0]/lyso_fit_pars[0]
            dspe = spe_fit_par_errors[3]/spe_fit_pars[3]
            dtotal = np.sqrt(dlyso**2 + dspe**2)
            yerr.append(y[-1]*dtotal)




                
                        
