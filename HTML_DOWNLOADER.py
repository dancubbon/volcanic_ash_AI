import pandas as pd
import datetime as dt
import wget
import subprocess

v_dict = {'NISHINOSHIMA': 28409600, 'SAKURAJIMA (AIRA CALDERA)': 28208001, 'KARYMSKY': 30013000, 'EBEKO': 29038000,
          'KLYUCHEVSKOY': 30026000, 'SHEVELUCH': 30027000, 'SUWANOSEJIMA': 28203000, 'BEZYMIANNY': 30025000,
          'SATSUMA-IOJIMA (KIKAI CALDERA)': 28206000, 'ASOSAN': 28211000, 'KUCHINOERABUJIMA': 28205000,
          'TAAL': 27307000, 'SEMISOPOCHNOI': 31106000, 'PAGAN': 28417000, 'CHIRINKOTAN' : 29026000,
          'FUKUTOKU-OKA-NO-BA': 28413000, 'SARYCHEV PEAK': 29024000, 'SINABUNG': 26108000, 'NOTICE': 00000000,
          'TEST': 10000001}

v_list = v_dict.keys()

print("Searching for eruptions from the following volcanoes: ")
print(v_list)

# Get archive list.  replace year as necessary
url = 'https://ds.data.jma.go.jp/svd/vaac/data/vaac_list.html'
link_base = 'https://ds.data.jma.go.jp/svd/vaac/data/TextData/2021/'  # All of the text file links are preceded by this
table = pd.read_html(url)

df = table[2]  # use index 1 if in archives or 2 if recent


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

    # Extract the information needed to make the link to download each file
    datetime = row['Date Time']
    datetime_str = datetime[0:4] + datetime[5:7] + datetime[8:10]

    # Every volcano on the website needs to be in the dictionary for this next bit to work.
    volc_name = row['Volcano']
    try:
        volc_no = v_dict[volc_name]
    except KeyError:
        print("Volcano not in dictionary, skipping.")
        volc_no = 00000000

    adv_no = row['Advisory Number'][5:].zfill(4)

    # create the link format which the VAAC html files are stored as
    link_head = datetime_str+"_"+str(volc_no)+"_"+adv_no+"_Text.html"

    # concatenate link base and link head to form the link you can download from
    link = link_base+link_head
    try:
        wget.download(link, 'D:\\2021_HTML')
        print(link)
    except Exception:
        pass


