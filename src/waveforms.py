#!/usr/bin/env python3
"""
GUI for controlling the Caltech BTL QA/QC jig.

Author: Anthony LaTorre
Last Updated: Jan 24, 2023
"""
from btl import Client
import random
from os.path import join, expanduser, exists, splitext
import os
import json
from subprocess import Popen, PIPE
import os
import h5py

import numpy as np


WAVEDUMP_PROGRAM = 'wavedump'
ANALYZE_WAVEFORMS_PROGRAM = 'analyze-waveforms'

# Debug mode. Right now this just controls whether we draw random numbers for
# polling.
DEBUG = False

# Assembly centers. This should be synchronized with the SQL file at
# ../website/btl_qa.sql.
ASSEMBLY_CENTERS = [
    "Caltech",
    "UVA",
    "Milano",
    "CERN",
    "Peking"
]

NUMBER_OF_BOARDS = [str(i) for i in range(1,5)]

# These sources should be kept the same as those in `analyze-waveforms`.
SOURCES = ['LYSO', 'Sodium', 'Cesium', 'Cobalt']

BOARD_ADDRESSES = {
    0: [0,1],
    1: [2,3],
    2: [4,5],
    3: [6,7],
}

RELAYS = [0,1,2,3,4,5]



def filename_template(data_path='./', barcode=None, ov=None, trigger=None, n_spe=None, n_source=None):
    print('filename 1')
    if not exists(data_path) and data_path != '':
        os.makedirs(data_path)
    return join(data_path, 'module_%i_Vov%.2f_Vtt%.3f_Nspe%d_Nsource%d.hdf5' % (int(barcode), float(ov), abs(trigger), int(n_spe), int(n_source)))

def print_warning(msg):
    if not msg.endswith('\n'):
        msg += '\n'
    print(msg)

def run_command(cmd, progress_bar=None):
    global stop
    stop = False
    print( " ".join(map(str,cmd)) + '\n')
    p = Popen(['stdbuf','-o0'] + list(map(str,cmd)), stdout=PIPE, stderr=PIPE)
    for line in iter(p.stdout.readline, b''):
        print(line.decode().rstrip('\n'))
        if stop:
            p.terminate()
            stop = False
    p.wait()
    if p.returncode != 0:
        print_warning(p.stderr.read().decode())
    return p.returncode

def save(filename=None):
    """
    Save the GUI state from the json file specified by `filename`.
    """
    # if filename is None:
    #     filename = join(expanduser("~"),".qaqc_gui.settings")
    # data = {}
    # data['assembly_center'] = assembly_center
    # data['source'] = source
    # data['n_boards'] = int(n_boards_var)
    # data['barcodes'] = [barcode for barcode in barcodes]
    # data['module_available'] = [available for available in module_available]
    # data['ov'] = ov
    # data['trigger'] = trigger
    # data['vbds'] = [vbd for vbd in vbds]
    # data['data_path'] = data_path
    # data['ip_address'] = ip_address
    # #data['stepper_enable'] = stepper_enable
    # data['n_spe_events'] = n_spe_events
    # data['n_source_events'] = n_source_events
    # data['upload'] = upload_enable
    # print("Saving GUI state from '%s'" % filename)
    # with open(filename,'w') as f:
    #     json.dump(data,f)

def load(filename=None):
    """
    Load the GUI state from the json file specified by `filename`.
    """
    # if filename is None:
    #     filename = join(expanduser("~"),".qaqc_gui.settings")
    # print("Loading GUI state from '%s'" % filename)
    # if exists(filename):
    #     with open(filename,'r') as f:
    #         data = json.load(f)
    #     if 'assembly_center' in data:
    #         assembly_center.set(data['assembly_center'])
    #     if 'source' in data:
    #         source.set(data['source'])
    #     if 'n_boards' in data:
    #         n_boards_var.set(str(data['n_boards']))
    #     if 'barcodes' in data:
    #         for i, barcode in enumerate(data['barcodes']):
    #             barcodes[i].set(barcode)
    #     if 'module_available' in data:
    #         for i, available in enumerate(data['module_available']):
    #             module_available[i].set(available)
    #     if 'ov' in data:
    #         ov.set(data['ov'])
    #     if 'trigger' in data:
    #         trigger.set(data['trigger'])
    #     if 'vbds' in data:
    #         for i, vbd in enumerate(data['vbds']):
    #             vbds[i].set(vbd)
    #     if 'data_path' in data:
    #         data_path.set(data['data_path'])            
    #     if 'ip_address' in data:
    #         ip_address.set(data['ip_address'])
    #     #if 'stepper_enable' in data:
    #     #    stepper_enable.set(data['stepper_enable'])
    #     if 'n_spe_events' in data:
    #         n_spe_events.set(data['n_spe_events'])
    #     if 'n_source_events' in data:
    #         n_source_events.set(data['n_source_events'])
    #     if 'upload_enable' in data:
    #         upload_enable.set(data['upload_enable'])
    #     n_boards_changed()

def on_closing():
    """
    Function to run before the window is closed. Right now we just save the GUI
    state and then quit the program.
    """
    save()

def query(client, cmd):
    print( "%s\n" % cmd)
    if not DEBUG:
        return client.query(cmd)

def hv_off(client):
    n_boards = int(n_boards_var)
    try:
        query(client, "disable_hv")
    except Exception as e:
        print_warning(str(e))
    # First, make sure all the HV relays are off
    for i in range(n_boards):
        for bus in BOARD_ADDRESSES[i]:
            for k in RELAYS:
                try:
                    query(client, "hv_write %i %i off" % (bus, k))
                except Exception as e:
                    print_warning(str(e))

STOP = False

def stop():
    global stop
    stop = True

def reanalyze_data():
    # Make sure they entered the barcodes first.
    for i in range(12):
        if not module_available[i]:
            continue

        barcode = barcodes[i]
        if barcode == '':
            print_warning('Need to enter a barcode for module %i\n' % i)
            return

    # Now, we analyze all the data
    for i in range(12):
        if not module_available[i]:
            print( "Skipping module %i\n" % i)
            continue

        barcode = barcodes[i]
        if barcode == '':
            print_warning('Need to enter a barcode for module %i\n' % i)
            return

        try:
            filename = filename_template(data_path=data_path, barcode=barcode, ov=ov, trigger=trigger, n_spe=n_spe_events, n_source=n_source_events)
        except:
            print('reanalyze_data')
            print_warning("Not a valid data path: %s\n" % data_path)
            return

        print( "Analyzing data for module %i\n" % int(barcode))

        root, ext = splitext(filename)
        root_filename = "%s.root" % root
        cmd = [ANALYZE_WAVEFORMS_PROGRAM,filename,'-o', root_filename]
        if run_command(cmd,progress_bar=i):
            print("Failed analysis")
            continue

        print("Data + analysis successful!")

def take_data():
    """
    Function to take single PE and 511 keV data for all the modules marked
    present in the GUI. First, we move the stepper motor, then take single PE
    data, then 511 data, and finally analyze it and upload the results to the
    database.
    """
    n_boards = int(n_boards_var)
    
    # Make sure they entered the barcodes first.
    for i in range(12):
        if not module_available[i]:
            continue

        barcode = barcodes[i]
        if barcode == '':
            print_warning('Need to enter a barcode for module %i\n' % i)
            return

        print("-")

    client = Client(ip_address)

    # First, we try to get the stepper to the home position
    #if stepper_enable:
    #    try:
    #        query(client, "step_home")
    #    except Exception as e:
    #        print_warning(str(e))
    #        return

    # Next, we take the single PE data
    try:
        query(client, "set_attenuation off")
    except Exception as e:
        print_warning(str(e))
        return

    # First, make sure all the HV relays are off
    hv_off(client)

    # Now, we turn them on one by one and take data
    for i in range(12):
        if not module_available[i]:
            print( "Skipping module %i\n" % i)
            continue
        
        barcode = barcodes[i]
        if barcode == '':
            print_warning('Need to enter a barcode for module %i\n' % i)
            return

        vbd = vbds[i]
        if vbd == '':
            print_warning('Need to enter a Vbd for module %i\n' % i)
            return

        hv = float(vbd)+float(ov)
        print('Setting absolute bias voltage %.2f for module %i\n' %(hv,i) )

        try:
            filename = filename_template(data_path=data_path, barcode=barcode, ov=ov, trigger=trigger, n_spe=n_spe_events, n_source=n_source_events)
        except:
            print('take_data 1')
            print(data_path, barcode, ov, trigger, n_spe_events, n_source_events)
            print_warning("Not a valid data path: %s\n" % data_path)
            return

        if exists(filename):
            print("deleting %s" % filename)
            os.unlink(filename)

        # Loop over first 8 channels and second eight channels
        for j in range(2):
            # Diagram to help figure out what's going on. It's drawn as if you
            # are looking top down at the modules plugged in:
            #
            #     Bus HV1 HV2 Module Bus HV1 HV2
            #     --- --- --- ------ --- --- ---
            #      2   0   1     5    3   4   5
            #      2   2   3     4    3   2   3
            #      2   4   5     3    3   0   1
            #
            #      0   0   1     2    1   4   5
            #      0   2   3     1    1   2   3
            #      0   4   5     0    1   0   1

            # Loop over left and right sides
            for k in range(2):
                bus = (i//3)*2 + k
                relay = (i % 3)*2 + j

                if k == 0:
                    # Ordering for the board on left side is backwards from the
                    # board on the right side
                    relay = 5 - relay

                try:
                    query(client, "hv_write %i %i on" % (bus, relay))
                except Exception as e:
                    print_warning(str(e))
                    return

            try:
                query(client, "set_hv %.2f" % hv )
            except Exception as e:
                print_warning(str(e))
                return

            # Turn the attenuation off to take SPE data
            try:
                query(client, "set_attenuation off")
            except Exception as e:
                print_warning(str(e))
                return

            if run_command([WAVEDUMP_PROGRAM,'-t','software','-l','spe','--channel-map',j % 2,'-n',n_spe_events,'-o',filename], progress_bar=i):
                hv_off(client)
                return

            # Turn the attenuation on to take source data
            try:
                query(client, "set_attenuation on")
            except Exception as e:
                print_warning(str(e))
                return

            try:
                voltage = query(client, "extmon_vread")
            except Exception as e:
                print_warning(str(e))
                return

            cmd = [WAVEDUMP_PROGRAM,'-t','self','-l',source.lower(),'--channel-map',j % 2,'-n',n_source_events,'-o',filename,'--threshold',trigger]
            if run_command(cmd, progress_bar=i):
                hv_off(client)
                return

            try:
                query(client, "disable_hv")
            except Exception as e:
                print_warning(str(e))
                return

            # Loop over left and right sides
            for k in range(2):
                bus = (i//3)*2 + k
                relay = (i % 3)*2 + j

                if k == 0:
                    # Ordering for the board on left side is backwards from the
                    # board on the right side
                    relay = 5 - relay

                try:
                    query(client, "hv_write %i %i off" % (bus, relay))
                except Exception as e:
                    print_warning(str(e))
                    return

        info = poll_single_module(client,i)

        with h5py.File(filename,"a") as f:
            for key, value in info.items():
                f.attrs[key] = value

            f.attrs['barcode'] = barcode
            f.attrs['voltage'] = voltage
            f.attrs['institution'] = assembly_center

        print("Data taking done")

    # Now, we analyze all the data
    for i in range(12):
        if not module_available[i]:
            print( "Skipping module %i\n" % i)
            continue

        barcode = barcodes[i]
        if barcode == '':
            print_warning('Need to enter a barcode for module %i\n' % i)
            return

        try:
            filename = filename_template(data_path=data_path, barcode=barcode, ov=ov, trigger=trigger, n_spe=n_spe_events, n_source=n_source_events)
        except:
            print('take_data 2')
            print_warning("Not a valid data path: %s\n" % data_path)
            return

        print( "Analyzing data for module %i\n" % int(barcode))
        
        

        root, ext = splitext(filename)
        root_filename = "%s.root" % root
        cmd = [ANALYZE_WAVEFORMS_PROGRAM,filename,'-o', root_filename]
        if run_command(cmd,progress_bar=i):
            print("Failed analysis")
            continue

        print("Data + analysis successful!")

def poll_single_module(client, module):
    values = {}
    # Loop over left and right sides
    for k in range(2):
        # Diagram to help figure out what's going on. It's drawn as if you
        # are looking top down at the modules plugged in:
        #
        #     Bus Thermistor Module Bus Thermistor
        #     --- ---------- ------ --- ----------
        #      2      0         5    3      2
        #      2      1         4    3      1
        #      2      2         3    3      0
        #
        #      0      0         2    1      2
        #      0      1         1    1      1
        #      0      2         0    1      0
        bus = (module//3)*2 + k
        thermistor = module % 3

        if k == 0:
            # Ordering for the board on left side is backwards from the
            # board on the right side
            thermistor = 2 - thermistor

        key = '_a' if k == 0 else '_b'

        try:
            thermistor_value = query(client, "thermistor_read %i %i" % (bus, thermistor))
            if DEBUG:
                thermistor_value = random.uniform(20,30)
        except Exception as e:
            print_warning(str(e))
            return

        try:
            # TECs are numbered backwards from thermistors
            tec_value = query(client, "tec_check %i %i" % (bus, 2-thermistor))
            if DEBUG:
                tec_value = random.uniform(7,10)
        except Exception as e:
            print_warning(str(e))
            return

        values['temp%s' % key] = thermistor_value
        values['tec%s' % key] = tec_value

    return values

def poll():
    """
    Read all the thermistor temperatures and the TEC resistance.
    """
    client = Client(ip_address)

    for i in range(12):
        if not module_available[i]:
            print("Skipping module %i" % i)
            for k in range(2):
                bus = (i//3)*2 + k
                thermistor = i % 3
                if k % 2 == 0:
                    thermistor_text[(i,'temp_a')].config(text="")
                    thermistor_text[(i,'tec_a')].config(text="")
                else:
                    thermistor_text[(i,'temp_b')].config(text="")
                    thermistor_text[(i,'tec_b')].config(text="")
            continue

        values = poll_single_module(client, i)

        if values is None:
            return

        for key, value in values.items():
            print("i, key = ", i, key)
            print("value = ", value)
            thermistor_text[(i,key)].config(text="%.2f" % value)

def step_home():
    client = Client(ip_address)
    try:
        query(client, "step_home")
    except Exception as e:
        print_warning(str(e))
        return

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser("BTL QA/QC GUI")
    #parser.add_argument("--debug", action='store_true', help='debug')
    args = parser.parse_args()

    #if args.debug:
    #    DEBUG = True
    #    WAVEDUMP_PROGRAM = './wavedump-test'
    #    ANALYZE_WAVEFORMS_PROGRAM = './wavedump-test'

    assembly_center = ASSEMBLY_CENTERS[0]
    source = SOURCES[1]#args['source']
    ip_address = '192.168.0.177'
    data_path = '/home/cptlab/qaqc-gui_output/scan'


    #! Make sure the barcodes are in the right order!!!
    barcodes = [200041, 100026, 200042] + [0 for i in range(12-3)]
    vbds = [38.25, 37.8, 37.8] + [37.8 for i in range(12-3)]
    module_available = [True, False, False] + [False for i in range(12-3)]
    n_boards_var = sum(module_available)
    barcode = barcodes[0]

    n_spe_events = 100_000
    n_source_events = 200_000
    #generate RDF info with timing info and saturation flag, separate RDF for each source/trigger group
    #computeTiming, mergeRDFs, computeSaturation = True, False, True 

    print('Waveforms settings:')
    print('  source=',source)
    print('  n_spe_events=',n_spe_events)
    print('  n_source_events=',n_source_events)
    print('  barcodes=',barcodes)
    print('  vbds=',vbds)
    print('  module_available=',module_available)
    
    thermistor_labels = {}
    thermistor_text = {}
    
    ovs = np.arange(1, 3 + 0.2, 0.2)
    triggers = np.arange(-0.100, -0.005 + 0.005, 0.005)
    print(f'{len(triggers) * len(ovs):,} total OV/TT combinations')
    # rng = np.random.default_rng()
    print(ovs)
    print(triggers)
    ov_tt_grid = np.array(np.meshgrid(ovs, triggers)).T.reshape(-1,2)
    # rng.shuffle(ov_tt_grid, axis=0)
    np.random.shuffle(ov_tt_grid)

    import multiprocessing
    import pickle
    import time
    scan_log = []

    for ov, tt in ov_tt_grid:
        trigger = tt
        filename = filename_template(data_path=data_path, barcode=barcode, ov=ov, trigger=trigger, n_spe=n_spe_events, n_source=n_source_events)
        print(f'Taking data for ov=',ov,' and tt=',tt)
        # print('temperatures')
        # take_data()
        t_start = time.clock()
        p = multiprocessing.Process(target=take_data)
        p.start()
        p.join(1 * 60 * 60) # wait 1 hr or until take_data finishes
        t_end = time.clock()
        if p.is_alive():
            print('ov=',ov,' tt=',tt,' combination timed out -- killing')
            p.terminate()
        else:    
            root, ext = splitext(filename)
            print("Generating RDF")
            RDFFilename = "%s_RDF.root" % root
            #to remove timing info, remove '-c'. to remove saturation info, remove '--saturation_flag'
            #to merge RDataframes between trigger groups. add '-m'
            os.system("python3 waveforms_2.py {} -o {} -c --saturation_flag".format(filename, RDFFilename)) 
        os.system("rm -f "+filename)
        scan_log.append([ov, tt, t_end-t_start])

        with open('scan_log.csv', 'w') as fsl:
            fsl.write('ov, trigger, time\n')
            for _ov, _tt, _time in scan_log:
                fsl.write('%.2f, %.3f, %.1f\n' % (_ov, _tt, _time))

