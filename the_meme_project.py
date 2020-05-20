import numpy as np
import json
import requests, shutil
import glob, os

#
#   Slack allows for exporting of all messages posted in a given channel.
#   The export is given in a .json format, one .json-file for each day, which contains meta-data for each message.
#   Most importantly urls for every image/video attached to a post.
#
#   This script downloads all images/videos found from Slack export .json-files.
#   This is useful because the free version of Slack only allows for finite amount of messages,
#   before it starts deleting the oldest ones.
#
#   Directory of the .json-files, as well as wanted directory for downloaded
#   images/videos, must be changed in the global variables below.
#

CURRENT_DIR = os.path.dirname(__file__) # Finds the directory in which this python-file is located
JSON_DIR = CURRENT_DIR + r'/jsons/'     # Location of the folder containing all .json-files from the Slack export.
IMAGE_DIR = CURRENT_DIR + r'/images/'   # Directory where the images will be downloaded to

def collect_files() -> list:    # Finds all .json files from folder
    return [file_name for file_name in os.listdir(JSON_DIR)]

def open_json(file_name: str) -> list:   # Opens a given .json file -> Returns the .json as a list of dictionaries
    try:
        jsons = open(JSON_DIR + file_name,'r',encoding="utf8")
        return json.load(jsons)
    except Exception as e:
        print("Error opening json-file")
        print("File name:",file_name)
        print("Exception:",e)
        return []

def process_json(json_file: list) -> dict:  #Extracts all relevant data from all Slack messages encoded in a given (opened) json-file. Most importantly: the image urls
    slack_messages = {"urls": [],
                     "file_types": [],
                     "file_names": []}

    for j in json_file:
        if j["type"] == 'message':
            if "files" in j.keys():
                for message_file in j["files"]:
                    if "url_private" in message_file.keys():
                        slack_messages["urls"].append(message_file["url_private"])
                        slack_messages["file_types"].append(message_file["filetype"])
                        slack_messages["file_names"].append(message_file["name"])
    return slack_messages

def download_image(url: str, image_name: str):  #Downloads an image from a given image url
    resp = requests.get(url, stream = True)
    image_file = open(IMAGE_DIR + image_name,'wb')

    resp.raw.decode_constant = True

    shutil.copyfileobj(resp.raw, image_file)

    del resp

def download_all_images_from_json(json_file: list, date: str): #Downloads all images from a given (processed) .json-file
    slack_messages = process_json(json_file)

    if len(slack_messages["urls"]) > 0:
        for i, url in enumerate(slack_messages["urls"]):
            try:
                name_str = date + r'_' + str(i+1) + '.' + slack_messages["file_types"][i]   # Naming format for the Slack messages export-files is "YYYY-MM-DD.json", f.ex. "2018-04-25.json"
                download_image(url,name_str)                                                # Image files are here then named as "YYYY-MM-DD_(i+1).png", or with other appropriate file types

            except Exception as e:
                print("Error downloading image")
                print("Url:",url)
                print("Exception:",e)

def main():
    all_files = collect_files()

    n_files = len(all_files)

    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    for i, file_name in enumerate(all_files):
        date_str = file_name[:-5]
        json_file = open_json(file_name)
        download_all_images_from_json(json_file,date_str)
        print((i+1)*100 // n_files, "% done",sep='')
    print("100% done")

if __name__ == "__main__":

    main()
