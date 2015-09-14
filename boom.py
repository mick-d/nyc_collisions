import os
import pandas as pd
from pandas import read_csv
import matplotlib  
import matplotlib.pyplot as plt  
from matplotlib import rcParams 

project_dir='/home/michael/python_projects'
print('--- Reading data')
df = read_csv(os.path.join(project_dir, 'nyc_collisions_data/NYPD_Motor_Vehicle_Collisions.csv'))
timefigs_path=os.path.join(project_dir,'nyc_collisions/analysis/time')
print('--- Creating time interval ID')
df_longlat = df[pd.notnull(df['LONGITUDE']) & pd.notnull(df['LATITUDE'])]
df_longlat['TIME'] = pd.to_datetime(df_longlat['TIME'])
#df_longlat_squeezed = df_longlat.ix[:, ["LONGITUDE", "LATITUDE"]]
acc_time = pd.DatetimeIndex(df_longlat['TIME'])
interv_mins = 60
df_longlat['TIME_CAT'] = (acc_time.hour * 60 + acc_time.minute) // interv_mins

# Create map (no geo transform) configuration
pd.options.display.mpl_style = 'default' #Better Styling  
new_style = {'grid': False} #Remove grid  
matplotlib.rc('axes', **new_style)  
rcParams['figure.figsize'] = (17.5, 17) #Size of figure  
rcParams['figure.dpi'] = 600
print('--- Plotting all collisions')
P=df_longlat.plot(kind='scatter', x='LONGITUDE', y='LATITUDE',color='white',xlim=(-74.06,-73.77),ylim=(40.61, 40.91),s=3.5,alpha=.4)
#tt=plt.scatter(df_longlat['LONGITUDE'], df_longlat['LATITUDE'], color='white',s=3.5,alpha=.4)
#tt.xlim=[-74.06,-73.77]
#tt.ylim=[40.61, 40.91]
P.set_axis_bgcolor('black') #Background Color
print('--- Saving figure')
fig = plt.gcf()
fig.savefig(timefigs_path+'all_collisions.png')

# Calc stats
#df_longlat_timeidx = df_longlat.set_index('TIME')
#df_longlat_timeidx.groupby(pd.TimeGrouper('30Min'))['NUMBER OF PERSONS INJURED'].sum()





