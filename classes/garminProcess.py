import pandas as pd
import glob
import os
from pathlib import Path

#CONVERT WILL CALL SHELL SCRIPT TO CONVERT .FIT FILES TO CSV FILES
class Convert:
    def __init__(self,data_dir,garmin_java):
        #DATA_DIR CONTAINS THE FOLDERS WITH .FIT FILES IN THEM
        #GARMIN_JAVA POINTS TO THE .JAR FILE FROM THE GARMIN FITSDK
        input_files = data_dir + "/*.fit"
        files = glob.glob(input_files)
        for file in files:
            call = "java -jar " + garmin_java + " --defn none --data record '" + file + "'"
            os.system(call)

#COMBINE WILL READ .CSV FILES, RENAME/RESTRUCTURE VARIABLES AS NECESSARY, AND PUT ALL INTO ONE EXCEL FILE
class Combine:
    def __init__(self,data_dir,output):
        self.saver = pd.DataFrame() #WILL HOLD ALL DATA
        input_files = glob.glob(data_dir + "/*_data.csv") #DIRECTORY CONTAINING ALL THE POST-PROCESSED CSV FILES

        for file in input_files:
            temp = pd.read_csv(file)
            temp['datetime'] = convert_ts(temp['record.timestamp[s]']) #SEE FXN BELOW
            temp['id'],temp['condition'] = get_id(file) #SEE FXN BELOW
            temp.rename(columns={'record.heart_rate[bpm]': 'bpm'}, inplace=True) #RENAME TO SOMETHING USEFUL
            temp = temp[['id','condition', 'datetime','bpm']] #CLEAN UP AND SAVE
            self.saver = pd.concat([self.saver, temp])
        makedirs(output) #THIS WILL MAKE SURE THE OUTPUT FOLDER EXISTS BEFORE WRITING TO IT
        output_file = output + "full.xlsx"
        self.saver.to_excel(output_file,index=False)


def convert_ts(ts):
    #THE GARMIN TIMESTAMPS ARE SECONDS SINCE 12/31/1989
    return pd.to_datetime("December 31, 1989") + pd.to_timedelta(ts,unit='s')

def get_id(path):
    #ASSUMES FOLDER STRUCTURE IS PID_CONDITION - SPLIT ON UNDERSCORE AND RETURN AS INTEGER AND STRING
    pid,condition = (path.split(os.sep)[6]).split("_")
    pid = int(pid)
    return [pid,condition]

def makedirs(dir):
    Path(dir).mkdir(parents=True, exist_ok=True)