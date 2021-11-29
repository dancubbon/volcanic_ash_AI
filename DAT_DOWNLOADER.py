from VAA_HTML import download_command
from VAA_HTML import download_list_reduced
from VAA_HTML import coords_file_pairs
import subprocess
import numpy as np
print("Enter the name of the directory where your .HTML files are stored :")
html_dir = str(input("--> "))
print("Enter the name of the directory where you would like you .DAT files to be downloaded to:")
data_dir = str(input("--> "))
print("Enter \"list\" if you would like a list of all the aws download files: ")
print("Enter \"download_all\" if you would like to download all the files automatically")
print("Enter \"download_north\" if you would like to download all the files for the north hemisphere")
print("Enter \"download_minimum\" if you want to download only the files needed to make the square")
ans = str(input("--> "))
if ans == "list":
    download_list = download_command(html_dir,data_dir)
    for command in download_list:
        print(command)
if ans == "download_all":
    download_list = download_command(html_dir,data_dir)
    for command in download_list:
        subprocess.run(command)
if ans == "download_north":
    download_list = download_command(html_dir,data_dir)
    new_download_list = []
    for command in download_list:
        for i in [1,2,3,4,5]:
            command_strings = command.split(" ")
            command_strings.insert(4 , "--exclude \"*\" --include \"*S0" + str(i) + "10*\"" )
            new_download_list.append(" ".join(command_strings))
    for new_command in new_download_list:
        subprocess.run(new_command)
if ans == "download_minimum":
    filefmt_segment_pairs = download_list_reduced(html_dir)
    data = coords_file_pairs(html_dir)
    download_list = download_command(html_dir, data_dir)
    new_download_list = []
    for pair in filefmt_segment_pairs:
        filefmt = pair[0]
        segment = pair[1]
        command_base = "undefined yet"
        for x in data:
            if x[0] == filefmt:
                command_base = x[3]
        command_split = command_base.split(" ")
        command_split.insert(4, "--exclude \"*\" --include \"" +segment+ "\"" )
        reduced_command = " ".join(command_split)
        new_download_list.append(reduced_command)
    fileset_count = len(new_download_list)
    for z in new_download_list[1104:]:
        subprocess.run(z)
        print("Downloaded fileset " + str(new_download_list.index(z) + 1) + " of " + str(fileset_count + 1) + " ... " +
              str(np.round((100*(new_download_list.index(z)+1)/(fileset_count+1)),2)) + " %")

        # On ethernet it takes about 33 seconds to download all the data for a dataset (mostly searching!)
        # On my computer it takes about 40 seconds per dataset to generate the ash map
        # The data takes up about 1/8 of a GB per dataset on the disk


