import pandas as pd
import glob
import os
from pathlib import Path

class Convert:
    def __init__(self,data_dir,garmin_java):
        input_files = data_dir + "/*.fit"
        files = glob.glob(input_files)
        for file in files:
            call = "java -jar " + garmin_java + " --defn none --data record '" + file + "'"
            os.system(call)

class Combine:
    def __init__(self,data_dir,output):
        self.saver = pd.DataFrame()
        input_files = glob.glob(data_dir + "/*_data.csv")
        for file in input_files:
            temp = pd.read_csv(file)
            temp['datetime'] = convert_ts(temp['record.timestamp[s]'])
            temp['id'],temp['condition'] = get_id(file)
            temp.rename(columns={'record.heart_rate[bpm]': 'bpm'}, inplace=True)
            temp = temp[['id','condition', 'datetime','bpm']]
            self.saver = pd.concat([self.saver, temp])
        makedirs(output)
        output_file = output + "full.xlsx"
        self.saver.to_excel(output_file,index=False)


def convert_ts(ts):
    return pd.to_datetime("December 31, 1989") + pd.to_timedelta(ts,unit='s')

def get_id(path):
    pid,condition = (path.split(os.sep)[6]).split("_")
    pid = int(pid)
    return [pid,condition]

def makedirs(dir):
    Path(dir).mkdir(parents=True, exist_ok=True)