from VAA_HTML import download_command
import subprocess
print("Enter the name of the directory where your .HTML files are stored :")
html_dir = str(input("--> "))
print("Enter \"list\" if you would like a list of all the aws download files: ")
print("Enter \"download_all\" if you would like to download all the files automatically")
ans = str(input("--> "))
if ans == "list":
    download_list = download_command(html_dir)
    for command in download_list:
        print(command)
if ans == "download_all":
    download_list = download_command(html_dir)
    for command in download_list:
        subprocess.run(command)
