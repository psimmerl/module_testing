# CMS Barrel Timing Layer (BTL) Module Analysis @ Caltech
- contact: paul simmerling
    - email: [psimmerl@caltech.edu](mailto:psimmerl@caltech.edu)


## Environment
---
`conda create --name <env> --file requirements.txt`

python


# Notes on data acquistion
> [!warning] faq
> if the source data has poission statistics check which source is in the dark box

Settings:
```
Unless otherwise specified assume Vbd = 37.8V

ov = 2.00V:
    SPE delay = XXXms
    LYSO   tr = -0.XXV
    SODIUM tr = -0.XXV
        tr = -0.01V -> Ch0: Nev = X, Speak/Bpeak = X/X, S/sqrt[B] = X.X
        tr = -0.02V -> 
        tr = -0.03V -> Ch0: Nev = X, Speak/Bpeak = X/X, S/sqrt[B] = X.X
        tr = -0.04V -> Ch0: Nev = X, Speak/Bpeak = X/X, S/sqrt[B] = X.X
        tr = -0.05V -> 
        tr = -0.10V -> 
        tr = -0.20V -> 
    CESIUM tr = -0.XXV
    COBALT tr = -0.XXV
ov = 4.20V: some events saturate amplifiers
    SPE delay = XXXms
    LYSO   tr = -0.05V
    SODIUM tr = -0.20V
        tr = -0.20V -> Ch0: Nev = 19225, Speak/Bpeak = 275/100, S/sqrt[B] = 27.5
    CESIUM tr = -0.20V
    COBALT tr = -0.20V

tr = -0.08V -> Ch0: Nev = 19068, Speak/Bpeak = 220/160, S/sqrt[B] = 10.79
```



<!--
## sphinx docstring
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
