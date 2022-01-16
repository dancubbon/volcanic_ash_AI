from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import subprocess
from VAA_HTML import get_vaac_data
from VAA_HTML import download_command
from LABELLED_DATASET_MAKER import generate_ash_map
from LABELLED_DATASET_MAKER import generate_btd_map

wv_correction_type = "static_wv_correction"
# my_ash_map_info = generate_ash_map("D:\Test_html_folder","D:\Test_download_folder",0,"partial",wv_correction_type)
# my_ash_map = my_ash_map_info[0]
# my_ash_map_date = my_ash_map_info[1][1:14]
# print("Verifying data date: ")
# print(str(my_ash_map_date))
# plot_title = "ASH_MAP_" + str(wv_correction_type) + "_" + str(my_ash_map_date) + ".png"
# print("plot will be titled: " + str(plot_title))
# plt.imshow(my_ash_map,vmin=-5, vmax=5, cmap='RdBu')
# plt.title(plot_title)
# plt.imsave(plot_title, my_ash_map,vmin=-5, vmax=5, cmap='RdBu')
# plt.show()


def make_full_data_set(html_folder, dat_folder, labelled_dataset_folder, wv_correction, show_image, download_required):
    # html_folder = filepath that your html files are in
    # dat_folder = location of himawari data (.DAT/.bz2)
    # labelled_dataset_folder = location you wish the .txt files to be saved to
    # wv_correction = type of water vapour correction. "no_wv_correction" "static_wv_correction" "dynamic_wv_correction"
    # show_image = 0 if you don't want to save the images 1 if you do
    # download_required = 0 if you already have the data, 1 if you don't ye
    html_file_count = len(get_vaac_data(html_folder))
    print("number of files: " + str(html_file_count))
    for i in range(html_file_count):
        print("current file number: " + str(i+1))
        if download_required == 1:
            print("Download requested for file " + str(i+1))
            download_list = download_command(html_folder, dat_folder)
            file_to_be_downloaded = download_list[i]
            subprocess.run(file_to_be_downloaded)
        print("approximate time remaining (ignoring any download times): " + str(2*(html_file_count-i)) + " minutes.")
        data = generate_ash_map(html_folder, dat_folder, i, "full", wv_correction)
        ash_data = data[0].tolist(0)
        filename = str(get_vaac_data(html_folder)[i][0][1:14]) + "_" + str(wv_correction) + ".txt"
        pngname = str(get_vaac_data(html_folder)[i][0][1:14]) + "_" + str(wv_correction) + ".png"
        filename_with_path = str(Path(labelled_dataset_folder + "\\" + filename))
        # f = open(filename_with_path,'x') # will return an error if the file already exists
        f = open(filename_with_path, 'w')  # will write the file again even if it already exists
        f.write(str(ash_data))
        f.close()
        if show_image == 1:
            plt.imshow(data[0], vmin=-5, vmax=5, cmap='RdBu')
            plt.title(filename)
            print("file will be saved as: " + str(pngname))
            plt.imsave(pngname, data[0])
            plt.show()
        # labelled_dateset


make_full_data_set("D:\Test_html_folder", "D:\Test_download_folder",
                   "D:\Test_labelled_dataset_folder", wv_correction_type, 1, 0)