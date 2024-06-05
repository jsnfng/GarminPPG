import pandas as pd
import numpy as np
import classes.garminProcess as gp #THIS HANDLES CONVERTING .FIT FILES AND MERGING INTO ONE DATAFRAME

#FILES AND LOCATIONS
#DEFINES START/END OF E/ BOUT BASED ON STOPWATCH OR VISUAL INSPECTION OF ECG
list_comparison = pd.read_excel("limits.xlsx")
data_dir = "/volumes/Drive2/Garmin PPG/garminProcess/input_data/*" #WHERE ARE .FIT FILES STORED?
garmin_location = "FitSDKRelease_21.60.00/java/FitCSVTool.jar" #LOCATION OF THE GARMIN FIT SDK
output_dir = "Output/" #WHERE WILL OUTPUT FILES BE SAVED?
longform_name = "longform_6.5.24.xlsx" #NAME OF THE LONGFORM EXCEL FILE TO BE SAVED
wideform_name = "wideform_6.5.24.xlsx" #NAME OF THE WIDEFORM EXCEL FILE TO BE SAVED
ids=[1,2,3,4,5,6,7,8,9,10,104,107,110,112,113,114,117,118,119,120,121] #PARTICIPANT IDS TO BE INCLUDED
summary = pd.DataFrame() #THIS WILL COMBINE DATA FROM EACH PARTICIPANT

#PROCESS DATA
# UNCOMMENT IF .FIT FILES NEED TO BE CONVERTED
#gp.Convert(data_dir,garmin_location)

#UNCOMMENT IF PROCESSED .FIT FILES NEED TO BE COMBINED; RETURNS A DATAFRAME THAT CAN BE USED INSTEAD OF IMPORTING XLSX
garmin = gp.Combine(data_dir,output_dir)
all_data = garmin.saver

# all_data = pd.read_excel(output_dir + "full.xlsx") #IF THE COMBINE STEP IS NOT USED THEN YOU CAN IMPORT THE XLSX HERE

#NOW PROCESS DATA

#EXTRACT SEPARATE CHEST AND PPG DATA AND SORT BY DATETIME AND PID; RENAME COLUMNS FOR LATER CLARITY
chest, watch = [x for _, x in all_data.groupby(all_data['condition'] == "W")]
chest.sort_values(by=['datetime', 'id'], inplace=True)
watch.sort_values(by=['datetime', 'id'], inplace=True)
watch = watch.rename(columns={'bpm': 'watchBPM'})
chest = chest.rename(columns={'bpm': 'chestBPM'})

#BE SURE WE ARE IN USABLE DATETIME FORMAT
chest['date'] = pd.to_datetime(chest['datetime'], utc=True).dt.date
chest['time'] = pd.to_datetime(chest['datetime'], utc=True).dt.time
watch['date'] = pd.to_datetime(watch['datetime'], utc=True).dt.date
watch['time'] = pd.to_datetime(watch['datetime'], utc=True).dt.time

#MERGE ON THE CLOSEST TIMESTAMP, UP TO 5S DIFFERENCE
combined_conditions = pd.merge_asof(chest, watch, on="datetime", by="id", tolerance=pd.Timedelta("5s"))

#LOOP THROUGH IDS TO BE INCLUDED
for id in ids:
    #CREATE A DATAFRAME WITH JUST THIS PID TO EXTRACT OUT DATA BY PHASE AND PROCESS
    print(id)
    one_id = combined_conditions.loc[combined_conditions['id'] == id]
    print(combined_conditions)
    print(one_id)
    #add a row-number column for easy referencing on the plot
    one_id['row_num'] = np.arange(len(one_id))

    #make row-number the index
    one_id.set_index("row_num")

    #PULL OUT LABELS FOR EACH PERIOD FOR THIS PID AND THEN CATEGORIZE
    ramp1 = list_comparison.loc[list_comparison['PID'] == id, 'ramp1'].values[0]
    exercise_start = list_comparison.loc[list_comparison['PID'] == id, 'exerciseStart'].values[0]
    exercise_end = list_comparison.loc[list_comparison['PID'] == id, 'exerciseEnd'].values[0]
    rest_end = list_comparison.loc[list_comparison['PID'] == id, 'restEnd'].values[0]
    ramp2 = list_comparison.loc[list_comparison['PID'] == id, 'ramp2'].values[0]
    exercise_2_end = list_comparison.loc[list_comparison['PID'] == id, 'exercise2End'].values[0]

    # CATEGORIZE BY BINS
    one_id['category'] = pd.cut(one_id['row_num'],
                                 bins=[0, ramp1, exercise_start, exercise_end, rest_end, ramp2, exercise_2_end],
                                 labels=['start', 'ramp1', 'exercise1', 'rest', 'ramp2', 'exercise2'])

    #MAKE SOME COMPUTATIONS
    one_id['dif'] = one_id['chestBPM'] - one_id['watchBPM'] #HIGHER DIFFERENCE MEANS HIGHER ECG VS PPG
    one_id['ave'] = (one_id['chestBPM'] + one_id['watchBPM']) / 2 #AVERAGE THE TWO READINGS
    one_id['perc_dif'] = one_id['dif'] / one_id['chestBPM'] #GET THE PERCENT DIFFERENCE RELATIVE TO CHEST, WHICH IS OUR REFERENT

    #PULL OUT RELEVANT COLUMNS
    one_id = one_id[["id", "chestBPM", "watchBPM", "row_num", "ave", "dif", "perc_dif", "category"]]

    #AVERAGE FOR THIS PERSON W/IN E/ CATEGORY
    summarized = one_id.groupby("category", as_index=False,observed=True).mean()
    summarized['id'] = id
    #PUSH TO THE HOLDER DATAFRAME
    summary = pd.concat([summary, summarized], ignore_index=True)

#CREATE FINAL LONG AND WIDEFORM DATAFRAMES AND THEN WRITE
summary_trimmed = summary[["id", "category", "ave", "dif", "perc_dif","chestBPM","watchBPM"]]
summary_trimmed_wide = pd.pivot(summary_trimmed, index='id', columns='category').reset_index()

#WRITE TO EXCEL
summary_trimmed.to_excel(output_dir + longform_name, index=False)
summary_trimmed_wide.to_excel(output_dir + wideform_name, index=True)
