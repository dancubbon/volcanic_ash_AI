import pandas as pd
import datetime as dt
import wget
import subprocess

v_dict = {'NISHINOSHIMA': 28409600, 'SAKURAJIMA (AIRA CALDERA)': 28208001, 'KARYMSKY': 30013000, 'EBEKO': 29038000,
          'KLYUCHEVSKOY': 30026000, 'SHEVELUCH': 30027000, 'SUWANOSEJIMA': 28203000, 'BEZYMIANNY': 30025000,
          'SATSUMA-IOJIMA (KIKAI CALDERA)': 28206000, 'ASOSAN': 28211000, 'KUCHINOERABUJIMA': 28205000,
          'TAAL': 27307000, 'SEMISOPOCHNOI': 31106000, 'PAGAN': 28417000, 'CHIRINKOTAN' : 29026000,
          'FUKUTOKU-OKA-NO-BA': 28413000, 'SARYCHEV PEAK': 29024000, 'SINABUNG': 26108000, 'NOTICE': 00000000}

v_list = v_dict.keys()

print("Searching for eruptions from the following volcanoes: ")
print(v_list)

# Get 2021 archive list
url = 'https://ds.data.jma.go.jp/svd/vaac/data/Archives/2020_vaac_list.html'
link_base = 'https://ds.data.jma.go.jp/svd/vaac/data/TextData/2020/'
table = pd.read_html(url)
df = table[1]

# Drop last header in array because it's 'Unnamed'
new_headers = df.keys().values[:-1]

# Drop the column with repeated datetime string
df = df.drop(['Volcano'], axis=1)

# Headers will now be wrong so we need to rename them
old_headers = df.keys().values
for old, new in zip(old_headers, new_headers):
    df = df.rename(columns={old: new})

# Print dataframe
print(df.head())

for index, row in df.iterrows():
    datetime = row['Date Time']
    datetime_str = datetime[0:4] + datetime[5:7] + datetime[8:10]
    volc_name = row['Volcano']
    volc_no = v_dict[volc_name]
    adv_no = row['Advisory Number'][5:].zfill(4)
    link_head = datetime_str+"_"+str(volc_no)+"_"+adv_no+"_Text.html"
    link = link_base+link_head
    try:
        wget.download(link)
        print(link)
    except Exception:
        pass


