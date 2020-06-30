import pandas as pd

# Ci = Concentracion inicial
# Cf = Concentracion final
# Vf = Volumen final
# Vi = Volumen incognita
# Vt = Volumen tampon

data = pd.read_csv("foo.csv")

def calculate_vi(row):
    return (row['Cf'] * row['Vf']) / row['Ci']

def calculate_vt(row):
    return row['vi'] - row['Vf']

data['vi'] = data.apply(calculate_vi, axis=1)
data['vt'] = data.apply(calculate_vt, axis=1)