# COMBINING FILES FROM TWO GARMIN DEVICES
This set of tools allows you to combine .fit files based on timestamps; in our case to compare data collected from ECG chest strap and on-device PPG. The protocol underlying the data processed with the script were collected from participants wearing a Polar H10 monitor
paired to one Garmin Forerunner 45, and PPG data collected on another Garmin Forerunner 45. Data were collected at rest, during a brief walking or jogging exercise bout, during a second rest period, and during a second exercise bout. 
## SETUP
### GARMIN DATA
This is structured to use two workout .fit files per participant and built on our folder organization that is detailed below.

### GARMIN FIT SDK
The first processing step involves passing each .fit file through Garmin's FIT SDK, which will convert each file to readable .csv. [Click Here](https://developer.garmin.com/fit/overview/) to access the FitSDK. You will point to the parent folder in the code.

### PACKAGES
Install the following python packages before running
- numpy
- pandas

### OTHER REQUIREMENTS
This also requires openpyxl to read/write to Excel.
```
pip install openpyxl
```
### FOLDER STRUCTURE
Use the project file structure. Regarding input .fit files, the code must be pointed to a data directory somewhere with the following structure
- Data (or whatever you want to call it)
  - Identifier 1_Condition
    - Identifier 1_Condition.fit
  - Identifier 2_Condition
    - Identifier 2_Condition.fit
   
The code is set up to handle condition 'C' for chest (ECG) and 'W' for wrist (PPG). The identifier is expected to be an integer. For example
  - 1_C
    -  1_C.fit
  - 1_W
    -  1_W.fit
  - 2_C
    -  2_C.fit
  - 2_W
    -  2_W.fit

### OTHER REQUIRED FILES
Within "inputs" there is a "limits.xlsx" Excel file. This will hold the <b>row number</b> within the dataframe corresponding to the _end_ of a given phase. For instance, the 'start' phase will likelybegin at row 0 and finish at the number given in the 'ramp' column for a given ID. 
These are the row number in the one_id dataframe corresponding to the start or end of a given bout as described below:
- Start: The period from when testing starts until when heart rate begins to climb due to the start of exercise.
- Ramp 1: The period in which heart rate values climb to steady-state during the first exercise bout.
- Exercise 1: Steady-state heart rate during the first exercise bout.
- Rest: The period of decreasing and then steady heart rate during the rest between exercise bouts.
- Ramp 2: The period in which heart rate values climb to steady-state during the second exercise bout.
- Exercise 2: Steady-state heart rate during the second exercise bout.

## RUNNING THE SCRIPT
The included "CreateFile.py" example script is commented to guide use.

First, import packages and processing classes
```
import pandas as pd
import numpy as np
import classes.garminProcess as gp #THIS HANDLES CONVERTING .FIT FILES AND MERGING INTO ONE DATAFRAME
```

Next, set up variables that point to input directories, output files, etc. Edit the capitalized information.
```
list_comparison = pd.read_excel("limits.xlsx")
data_dir = "/YOUR DIRECTORY/Data/*" #WHERE ARE .FIT FILES STORED?
garmin_location = "FitSDKRelease_21.60.00/java/FitCSVTool.jar" #LOCATION OF THE GARMIN FIT SDK
output_dir = "Output/" #WHERE WILL OUTPUT FILES BE SAVED?
longform_name = "longform_DATE.xlsx" #NAME OF THE LONGFORM EXCEL FILE TO BE SAVED
wideform_name = "wideform_DATE.xlsx" #NAME OF THE WIDEFORM EXCEL FILE TO BE SAVED
summary = pd.DataFrame() #THIS WILL COMBINE DATA FROM EACH PARTICIPANT
```

Create a list of participant ID numbers that will correspond to the integer IDs in your folder structure; 
include only those you want to include in your analyses.  
```
ids=[INSERT THE ID NUMBERS AS A LIST] #PARTICIPANT IDS TO BE INCLUDED
```

Next are the functions allowing you to process your .fit files and then to combine and process the resulting csv files.
```
# UNCOMMENT IF .FIT FILES NEED TO BE CONVERTED
#gp.Convert(data_dir,garmin_location)
#UNCOMMENT IF PROCESSED .FIT FILES NEED TO BE COMBINED; RETURNS A DATAFRAME THAT CAN BE USED INSTEAD OF IMPORTING XLSX
garmin = gp.Combine(data_dir,output_dir)
all_data = garmin.saver
```

Note that if you've already processed your data you can comment out the above lines and simply read in the processed excel file
```
all_data = pd.read_excel(output_dir + "full.xlsx") #IF THE COMBINE STEP IS NOT USED THEN YOU CAN IMPORT THE XLSX HERE
```
Next, extract out ecg and ppg rows and combine based on closest time stamps with a difference of up to 5 seconds
```
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
```

Loop through the IDs you'd like to include. For each one, categorize observations based on their phase in the study and then compute differences and averages. Note that percent difference
is based upon the ECG as the reference number.
```
#LOOP THROUGH IDS TO BE INCLUDED
for id in ids:
    #CREATE A DATAFRAME WITH JUST THIS PID TO EXTRACT OUT DATA BY PHASE AND PROCESS
    one_id = combined_conditions.loc[combined_conditions['id'] == id]
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
```

Finally, clean up and save a longform (each row contains a person and a specific category) and wide form (each row contains just a person with different columns for each phase) Excel file.
```
#CREATE FINAL LONG AND WIDEFORM DATAFRAMES AND THEN WRITE
summary_trimmed = summary[["id", "category", "ave", "dif", "perc_dif","chestBPM","watchBPM"]]
summary_trimmed_wide = pd.pivot(summary_trimmed, index='id', columns='category').reset_index()

#WRITE TO EXCEL
summary_trimmed.to_excel(output_dir + longform_name, index=False)
summary_trimmed_wide.to_excel(output_dir + wideform_name, index=True)
```
