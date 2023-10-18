#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import pandas as pd
import warnings
import pickle
from datetime import date, datetime, timedelta
warnings.filterwarnings("ignore")


#Function for initializing a hindcast
def Hindcast_Initialization(cwd, datapath, new_year, threshold, Region_list): 
    print('Creating files for a historical simulation within ', str(Region_list)[1:-1], ' regions for water year ', new_year)
    
    #Grab existing files based on water year
    prev_year = '2022'
    prev_date = prev_year + '-09-24'

    #input the new water year of choice
    new_year = str(int(new_year)-1)
    new_date = new_year + '-09-25'

    #threshold
    threshold = threshold

    #SWE_new = {}
    #for region in Region_list:
        #The below file will serve as a starting poinw
     #   SWE_new[region] = pd.read_hdf(f"{datapath}/data/PreProcessed/predictions{prev_year}-09-24.h5", key = region)
      #  SWE_new[region].rename(columns = {prev_date:new_date}, inplace = True)
       # SWE_new[region].to_hdf(f"{cwd}/Predictions/Hold_Out_Year/Predictions/predictions{new_year}-09-25.h5", key = region)
   

    #set the ground measures features DF    
    #obs_old = pd.read_csv(f"{datapath}/data/PreProcessed/ground_measures_features_{prev_year}-09-24.csv")
    #obs_old.rename(columns = {'Unnamed: 0':'station_id', prev_date:new_date}, inplace = True)
    #obs_old.set_index('station_id', inplace = True)
    #obs_old[new_date] = 0
    #obs_old.to_csv(f"{datapath}/data/PreProcessed/ground_measures_features_{new_year}-09-25.csv")
    #obs_old.to_hdf(f"{datapath}/data/PreProcessed/ground_measures_features.h5", key = f"{new_year}-09-25")

    #print('Ground measures features df complete')

    #load the ground_measures_features meta w/preds
    #obs_meta_old = pd.read_csv(f"{datapath}/data/PreProcessed/DA_ground_measures_features_{prev_year}-09-24.csv")
    #obs_meta_old.rename(columns = {'Unnamed: 0':'station_id'}, inplace = True)
    #obs_meta_old.set_index('station_id', inplace = True)
    #obs_meta_old['Date'] = new_date
    #obs_meta_old.to_csv(f"{datapath}/data/PreProcessed/DA_ground_measures_features_{new_year}-09-25.csv")
    #obs_meta_old.to_hdf(f"{datapath}/data/PreProcessed/DA_ground_measures_features.h5", key =f"{new_year}-09-25")
    #print('Ground measures features meta df complete')

    #Make a submission DF
    old_preds = pd.read_csv(f"{datapath}/data/PreProcessed/submission_format_{prev_date}.csv")
    old_preds['2022-10-01'] = 0
    new_preds_date = new_year+'-10-02'
    old_preds.rename(columns = {'2022-10-02':new_preds_date}, inplace = True)
    old_preds.set_index('cell_id', inplace = True)
    #old_preds.to_csv(f"{cwd}/Predictions/Hold_Out_Year/Predictions/submission_format_{new_date}.csv")
    old_preds.to_hdf(f"{cwd}/Predictions/Hold_Out_Year/Predictions/submission_format.h5", key =f"{new_date}")
    
    
    #define start and end date for list of dates
    start_dt = date(int(new_year), 10, 2)
    end_dt = date(int(new_year)+1, 6, 26)
    
    #create empty list to store dates
    datelist = []

    #append dates to list
    for dt in daterange(start_dt, end_dt):
        #print(dt.strftime("%Y-%m-%d"))
        dt=dt.strftime('%Y-%m-%d')
        datelist.append(dt)
        
     #makes sure all prediction locations for testing are included in the simulation   
    #addPredictionLocations(Region_list, datapath, cwd, datelist[0])
    
    print('New simulation start files complete')
    return datelist
    

    
#can be altered to create list every n number of days by changing 7 to desired skip length
def daterange(start_date, end_date):
     for n in range(0, int((end_date - start_date).days) + 1, 7):
        yield start_date + timedelta(n)
        
        
        
        
def HindCast_DataProcess(datelist,Region_list, cwd, datapath):
       #get held out year observational data
    Test = pd.DataFrame()
    cols = ['Date','y_test','Long', 'Lat', 'elevation_m', 'WYWeek', 'northness', 'VIIRS_SCA', 'hasSnow', 'Region']
    for Region in Region_list:
        T= pd.read_hdf(f"{datapath}/data/RegionWYTest.h5", Region)
        T['Region'] = Region
        #T['y_pred'] = -9999
        T.rename(columns = {'SWE':'y_test'}, inplace = True)
        T = T[cols]
        Test = pd.concat([Test, T])

        #Load predictions into a DF
    preds = pd.DataFrame()
    prev_SWE = pd.DataFrame()
    pred_sites = pd.DataFrame()
    TestsiteData = pd.DataFrame()
    TestsiteDataPSWE = pd.DataFrame()
    for date in datelist:
       # print(date)
        preds[date] = pd.read_hdf(f"{cwd}/Predictions/Hold_Out_Year/Predictions/2019_predictions.h5", key = date)
        
        #get previous SWE predictions for DF
        startdate = str(datetime.strptime(date, '%Y-%m-%d').date() -timedelta(7))
        if startdate < f"{startdate[:4]}-10-01":
            prev_SWE[startdate] = preds[date]
            prev_SWE[startdate] = 0
            
        else:
            prev_SWE[startdate] = pd.read_hdf(f"{cwd}/Predictions/Hold_Out_Year/Predictions/2019_predictions.h5", key = startdate)
        
        
        Tdata = Test[Test['Date'] == date]
        TestsiteData = pd.concat([TestsiteData, Tdata])
        
        
        try:
            prev_Tdata = Test[Test['Date'] == startdate]
            prev_Tdata['Date'] = date
            
        except:
            print('No previous observations for ', date)
        #add previous obs to determine prev_SWE error
        TestsiteDataPSWE = pd.concat([TestsiteDataPSWE, prev_Tdata])
        
        sites = Test[Test['Date'] == date].index
        #print(date, len(sites))
        #print(sites)
        
        for site in sites:
            #predictions
            s = pd.DataFrame(preds.loc[site].copy()).T
            s['Date'] = date
            s.rename(columns = {date:'y_pred'}, inplace = True)
            cols =['Date', 'y_pred']
            s = s[cols]
            
            #previous SWE
            pSWE = pd.DataFrame(preds.loc[site].copy()).T
            pSWE['Date'] = date
            pSWE.rename(columns = {startdate:'prev_SWE'}, inplace = True)
            cols =['Date', 'prev_SWE']
            pSWE = pSWE[cols]
            
            #print(s)
            s['prev_SWE'] = pSWE['prev_SWE']
            pred_sites = pd.concat([pred_sites, s])
         
    pswecols = ['Date', 'y_test']
    TestsiteDataPSWE = TestsiteDataPSWE[pswecols]
    TestsiteDataPSWE.rename(columns = {'y_test':'y_test_prev'}, inplace = True)
    #display(TestsiteDataPSWE)       
    
    #get predictions for obs locations
    cols = ['Date','y_test', 'y_test_prev', 'y_pred','prev_SWE','Long', 'Lat', 'elevation_m', 'WYWeek', 'northness', 'VIIRS_SCA', 'hasSnow', 'Region']
    #display(TestsiteData)
    TestsiteData = pd.concat([TestsiteData, pred_sites], axis =1)
    
    TestsiteData = TestsiteData.loc[:,~TestsiteData.columns.duplicated()].copy()
    TestsiteDataPSWE.reset_index(inplace = True)
    TestsiteData.reset_index(inplace = True)
    TestsiteData['Date'] = TestsiteData['Date'].dt.strftime('%Y-%m-%d')
    TestsiteData = pd.merge(TestsiteData, TestsiteDataPSWE,  how='left', left_on=['index','Date'], right_on = ['index','Date'])
    TestsiteData.set_index('index', inplace = True)
    TestsiteData.fillna(0, inplace = True)
    TestsiteData = TestsiteData[cols]
    TestsiteData['prev_SWE_error'] = TestsiteData['y_test_prev'] - TestsiteData['prev_SWE']
    #Set up dictionary to match the training data
    EvalTest = {}
    for Region in Region_list:
        EvalTest[Region] = TestsiteData[TestsiteData['Region'] == Region]
        EvalTest[Region]['y_pred_fSCA'] = EvalTest[Region]['y_pred']
    
    return  EvalTest
        

#function to add prediction locations in training dataset but not in the submission format file        
def addPredictionLocations(Region_list, datapath, cwd, startdate):
    print('Making sure all testing locations are in prediction dataframe.')
    #get held out year observational data
    Test = pd.DataFrame()
    cols = ['Date','y_test', 'y_pred','Long', 'Lat', 'elevation_m', 'WYWeek', 'northness', 'VIIRS_SCA', 'hasSnow', 'Region']
    for Region in Region_list:
        T= pd.read_hdf(f"{datapath}/data/RegionWYTest.h5", Region)
        T['Region'] = Region
        T['y_pred'] = -9999
        T.rename(columns = {'SWE':'y_test'}, inplace = True)
        T = T[cols]
        Test = pd.concat([Test, T])


    res = []
    [res.append(x) for x in list(Test.index) if x not in res]

    rows_not_pred = []
    for row in res:
        try:
            preds.loc[row]
        except:
            rows_not_pred.append(row)

    regions = pd.read_pickle(f"{datapath}\\data\\PreProcessed\\RegionVal.pkl")
    regionval = pd.DataFrame()
    Region_list2 = ['N_Sierras', 'S_Sierras']
    for region in Region_list2:
        regionval = pd.concat([regionval, regions[region]])
    regionval.set_index('cell_id', inplace = True)

    #get rows in Test that are not in regionVal
    Test2Rval = Test.copy()
    cols = ['Long','Lat','elevation_m', 'northness']
    Test2Rval = Test2Rval[cols]
    Test2Rval.drop_duplicates(inplace = True)
    Test2Rval = Test2Rval.loc[rows_not_pred]

    #add to regionval
    regionval = pd.concat([regionval, Test2Rval])
    regionval['Region'] = 'none'
    regionval.reset_index(inplace=True)
    #need to put back into respective regions and Region
    regionval = Region_id(regionval)
    regionval.rename(columns = {'index':'cell_id'}, inplace = True)
    regionval.set_index('cell_id', inplace = True)
    regionDict = {}
    for Region in Region_list2:
        regionDict[Region] = regionval[regionval['Region'] ==Region]
        regionDict[Region].pop('Region')
        regionDict[Region].reset_index(inplace = True)
     
    #set elevation based S_Sierras REgions
    regionDict['S_Sierras_Low'] = regionDict['S_Sierras'][regionDict['S_Sierras']['elevation_m'] <= 2500]
    regionDict['S_Sierras_High'] = regionDict['S_Sierras'][regionDict['S_Sierras']['elevation_m'] > 2500]

    # write the python object (dict) to pickle file
    path = f"{datapath}\\data\\PreProcessed\\RegionVal2.pkl"
    RVal = open(path, "wb")
    pickle.dump(regionDict, RVal)
    
    #Fix Predictions start DF
    startdate = datetime.strptime(startdate, '%Y-%m-%d').date() -timedelta(7)
    prev_SWE = {}
    for region in Region_list:
        prev_SWE[region] = pd.read_hdf(f"{cwd}\\Predictions\\Hold_Out_Year\\Predictions\\predictions{startdate}.h5", key =  region)                       

        pSWEcols = list(prev_SWE[region].columns) 
        rValcols = list(regionDict[region].columns)
        rValcols.remove('cell_id')
        res = [i for i in pSWEcols if i not in rValcols]
        for i in res:
            regionDict[region][i]=0
            
        #Final DF prep    
        regionDict[region]['WYWeek'] = 52  
        regionDict[region].set_index('cell_id', inplace = True)
        #save dictionary   
        regionDict[region].to_hdf(f"{cwd}\\Predictions\\Hold_Out_Year\\Predictions\\predictions{startdate}.h5", key = region)
                                              

           # return regionDict
    
    
def Region_id(df):

    # put obervations into the regions
    for i in range(0, len(df)):

        # Sierras
        # Northern Sierras
        if -122.5 <= df['Long'][i] <= -119 and 39 <= df['Lat'][i] <= 42:
            loc = 'N_Sierras'
            df['Region'].iloc[i] = loc

        # Southern Sierras
        if -122.5 <= df['Long'][i] <= -117 and 35 <= df['Lat'][i] <= 39:
            loc = 'S_Sierras'
            df['Region'].iloc[i] = loc
    return df

