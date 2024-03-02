# CMS Barrel Timing Layer (BTL) Module Analysis @ Caltech

Authors:
- Paul Simmerling, [psimmerl@caltech.edu](mailto:psimmerl@caltech.edu)
- Alex Albert
- Zichun Hao
- Kai Svensson
- Adolf Bornheim


# How to run this analysis
---

Notebooks (used to interact with & visualize data):
- `analyze_histos.ipynb`
    - use this to histograms generated from `qaqc_jig`'s `analyze-waveforms`

Tools (for terminal):
- `quick_draw.py`
- `makeLightYieldPlots.py`

## Python Environment
Use conda to create the environment

```bash
conda create --name qaqc --file requirements.txt
source env.sh # or `conda activate qaqc`
```

# Data Acquisition using the QAQC Jig
---

> [!warning] faq
> if the source data has poission statistics check which source is in the dark box


## Optimal/Working Settings
```
the metrics are from ch0 (eventually take averages)

Vbd = 37.8V

ov = 2.00V: rarely does an event saturate the opamp
    SPE delay = XXXms
    LYSO   tr = -0.XXV
    SODIUM tr = -0.XXV
    CESIUM tr = -0.XXV
    COBALT tr = -0.XXV
ov = 4.20V: many events saturate jig opamps
    SPE delay = XXXms
    LYSO   tr = -0.05V
    SODIUM tr = -0.20V
        tr =-0.20V -> 1023 evts/write -> N=19225, Spk/Ppk=275/100, S/sqrt[P]=27.5
    CESIUM tr = -0.20V
    COBALT tr = -0.20V
```

```
wavedump -t self -l sodium --channel-map 1 -n 400000 -o /home/cptlab/qaqc-gui_output/run231121/trig_200mV/module_100026_Vov2.20_Nspe200000_Nsodium400000.hdf5 --threshold -0.05
```

## Scanning Over-Voltage & Trigger Threshold

"Spk" = signal peak value, "Ppk" = pedestal peak value. idk if it is valid to compare exact values across runs/samples but comparing ratios should be okay

Test info:
- Module `100 026`
- Assumed a breakdown voltage (`Vbd`) of 37.8V
- Used a 10uC Sodium-22 test source (`CIT2204`)
- 100000 SPE events
- 200000 source events

| V OV | V Trig | S/√P | Notes |
| ---- | ------ | ---- | ----- |
| 1.2V | -0.XXV | XX.X |       |
| 1.4V | -0.XXV | XX.X |       |
| 1.6V | -0.XXV | XX.X |       |
| 1.8V | -0.XXV | XX.X |       |
| ---- | ------ | ---- | ----- |
| 2.0V | -0.XXV | XX.X |       |
| 2.2V | -0.XXV | XX.X |       |
| 2.4V | -0.XXV | XX.X |       |
| 2.6V | -0.XXV | XX.X |       |
| 2.8V | -0.XXV | XX.X |       |
| ---- | ------ | ---- | ----- |
| 3.0V | -0.XXV | XX.X |       |
| 3.2V | -0.XXV | XX.X |       |
| 3.4V | -0.XXV | XX.X |       |
| 3.6V | -0.XXV | XX.X |       |
| 3.8V | -0.XXV | XX.X |       |
| ---- | ------ | ---- | ----- |
| 4.0V | -0.XXV | XX.X |       |
| 4.2V | -0.XXV | XX.X |       |


Vov = 2.2V
| V Trig | ev/w | N evs | Spk/Ppk | S/√P |
| ------ | ---- | ----- | ------- |----- |
| -0.05V | XXXX | XXXXX | XXX/XXX | XX.X |
| -0.10V | XXXX | XXXXX | XXX/XXX | XX.X |
| -0.15V | XXXX | XXXXX | XXX/XXX | XX.X |
| -0.20V |   21 | XXXXX | XXX/XXX | XX.X |
| -0.25V | XXXX | XXXXX | XXX/XXX | XX.X |
| -0.30V | XXXX | XXXXX | XXX/XXX | XX.X |

Vov = 4.2V
| V Trig | ev/w | N evs | Spk/Ppk | S/√P |
| ------ | ---- | ----- | ------- |----- |
| -0.20V | 1023 | 19225 | 275/100 | 27.5 |


<!--
# more

## commands
Draw histogram from `analyze-waveform`'s output ROOT file:
```bash
export TEST_ROOT="module_XXXXXX_VovX.XX_NspeX_NsodiumX.root"
root -l $TEST_ROOT -e "sodium_ch0->Draw() ; c1->cd(1)->SetGrid()"
```

## documentation with sphinx
```python
def function(ParamName):
    """[Summary]

    :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
    :type [ParamName]: [ParamType](, optional)
    ...
    :raises [ErrorType]: [ErrorDescription]
    ...
    :return: [ReturnDescription]
    :rtype: [ReturnType]
    """
    ReturnValue = ParamName**2
    return ReturnValue
```
-->

