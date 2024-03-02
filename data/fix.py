import os


fs = os.listdir()
fs.remove('fix.py')
for f in fs:
    if 'Vtt' not in f:
        os.system(f'mv {f} {f.replace("Vov2.20","Vov2.20_Vtt25")}')

os.system('mkdir temp')
fs = os.listdir()
fs.remove('fix.py')
for f in fs:
    if '200042' in f:
        os.system(f'mv {f} temp/{f.replace("200042","200041")}')
    elif '200041' in f:
        os.system(f'mv {f} temp/{f.replace("200041","200042")}')

os.system('mv temp/* .')
os.system('rm -rf temp/')

