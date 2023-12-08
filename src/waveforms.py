"""waveforms

functions for acquiring and processing waveforms.


Scan over-voltages and trigger thresholds for a module.
1. Use wavedump (or acquire-waveforms?) to collect over-voltage and trigger threshold data for a chosen source type
    -   Save each waveform's integrated charge, if it's saturated, t_{10%}, t_{90%}, and anything else?
2. Analysis of integrated wave

"""
import os
import sys
import subprocess

sys.path.append("~/dt5742")
# sys.path.append("~/module_testing/")
# sys.path.append("~/module_testing/src")


import argparse
import numpy as np

# import scipy as sp

import ROOT as rt

IP_ADDRESS = ""


def acquire_waveforms(barcode, n_events, source: str = "sodium", ov: float = 2.2, tt: float = -0.05, **kwargs):
    """acquire_waveforms
    Acquire waveforms from the QAQC jig and saves to an hdf5 file.
    """

    assert tt < 0
    assert (ov < 5) and (ov > 0)

    t = "self"
    source = source.lower()

    channel_map = [1, 2, 3, 4]  # kwargs["channel_map"]

    vbd = 37.8
    hv = float(vbd) + float(ov)

    waveform_path = f"module{barcode}_Vov{ov:4.2f}_Vtt{abs(tt):3.2f}_N{source}{n_events}.hdf5"

    # if source in "spe":
    #     t = "self"  # not sel
    # else:  # self trigger for radioactive source
    if t == "self":
        pass

    client = Client(IP_ADDRESS)

    try:
        query(client, "set_attenuation off")
    except Exception as e:
        print_warning(str(e))
        return

    # First, make sure all the HV relays are off
    hv_off(client)

    # Now, we turn them on one by one and take data
    for i in range(12):
        print("Setting absolute bias voltage %.2f for module %i\n" % (hv, i))

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
                bus = (i // 3) * 2 + k
                relay = (i % 3) * 2 + j

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
                query(client, "set_hv %.2f" % hv)
            except Exception as e:
                print_warning(str(e))
                return

            # Turn the attenuation off to take SPE data
            try:
                query(client, "set_attenuation off")
            except Exception as e:
                print_warning(str(e))
                return

            if run_command(
                [
                    WAVEDUMP_PROGRAM,
                    "-t",
                    "software",
                    "-l",
                    "spe",
                    "--channel-map",
                    j % 2,
                    "-n",
                    n_spe_events.get(),
                    "-o",
                    filename,
                ],
                progress_bar=i,
            ):
                hv_off(client)
                return

            # Turn the attenuation on to take lyso data
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

            if run_command(
                [
                    WAVEDUMP_PROGRAM,
                    "-t",
                    "self",
                    "-l",
                    "lyso",
                    "--channel-map",
                    j % 2,
                    "-n",
                    n_lyso_events.get(),
                    "-o",
                    filename,
                ],
                progress_bar=i,
            ):
                hv_off(client)
                return

            try:
                query(client, "disable_hv")
            except Exception as e:
                print_warning(str(e))
                return

            # Loop over left and right sides
            for k in range(2):
                bus = (i // 3) * 2 + k
                relay = (i % 3) * 2 + j

                if k == 0:
                    # Ordering for the board on left side is backwards from the
                    # board on the right side
                    relay = 5 - relay

                try:
                    query(client, "hv_write %i %i off" % (bus, relay))
                except Exception as e:
                    print_warning(str(e))
                    return

        info = poll_single_module(client, i)

        with h5py.File(filename, "a") as f:
            for key, value in info.items():
                f.attrs[key] = value

            f.attrs["barcode"] = barcode
            f.attrs["voltage"] = voltage
            f.attrs["institution"] = assembly_center.get()

        module_status[i].config(text="Data taking done")

    # Now, we analyze all the data
    for i in range(12):
        if not module_available[i].get():
            entry.insert(tk.END, "Skipping module %i\n" % i)
            continue

        barcode = barcodes[i].get()
        if barcode == "":
            print_warning("Need to enter a barcode for module %i\n" % i)
            return

        try:
            filename = filename_template(
                data_path=data_path.get(),
                barcode=barcode,
                ov=ov.get(),
                n_spe=n_spe_events.get(),
                n_lyso=n_lyso_events.get(),
            )
        except:
            print_warning("Not a valid data path: %s\n" % data_path.get())
            return

        entry.insert(tk.END, "Analyzing data for module %i\n" % int(barcode))
        entry.yview(tk.END)
        entry.update()

        root, ext = splitext(filename)
        root_filename = "%s.root" % root
        cmd = [ANALYZE_WAVEFORMS_PROGRAM, filename, "-o", root_filename]
        if upload_enable.get():
            cmd += ["-u"]
        if run_command(cmd, progress_bar=i):
            module_status[i].config(text="Failed analysis")
            continue

        module_status[i].config(text="Data + analysis successful!")

        #########################

    for cmap in channel_map:
        wavedump_command = (
            f"wavedump -t {t} -l {source} --channel-map {cmap} -n {n_events} -o {waveform_path} --threshold {tt}"
        )
        subprocess.run(wavedump_command)

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
