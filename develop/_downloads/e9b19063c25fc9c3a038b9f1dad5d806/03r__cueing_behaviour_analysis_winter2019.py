"""
Cueing Behavioural Analysis Winter 2019
=======================================

"""


###################################################################################################
# Setup
# ---------------------
#

# Standard Pythonic imports
import os,sys,glob,numpy as np,pandas as pd
import matplotlib.pyplot as plt 
import scipy.io as sio 

# EEG-Notebooks imports
from eegnb.datasets import datasets

# sphinx_gallery_thumbnail_number = 1

###################################################################################################
# Download the data

eegnb_data_path = os.path.join(os.path.expanduser('~/'),'.eegnb', 'data')
cueing_data_path = os.path.join(eegnb_data_path, 'visual-cueing', 'kylemathlab_dev')

# If dataset hasn't been downloaded yet, download it
if not os.path.isdir(cueing_data_path):
      datasets.fetch_dataset(data_dir=eegnb_data_path, experiment='visual-cueing', site='kylemathlab_dev')



###################################################################################################
# Analyze .mat behavioural data for Accuracy and RT
# -----------------------------
#
# Load in subjects

# # Fall 2018
subs = [101, 102, 103, 104, 106, 108, 109, 110, 111, 112,
        202, 203, 204, 205, 207, 208, 209, 210, 211, 
        301, 302, 303, 304, 305, 306, 307, 308, 309]

# 105 - no trials in one condition

# # Winter 2019
# subs = [1101, 1102, 1103, 1104, 1105, 1106, 1108, 1109, 1110,
#         1202, 1203, 1205, 1206, 1209, 1210, 1211, 1215,
#         1301, 1302, 1313, 
#         1401, 1402, 1403, 1404, 1405,  1408, 1410, 1411, 1412, 1413, 1413, 1414, 1415, 1416]

# # 1107 - no csv session 1
# # 1201 - no csv session 1
# # 1304 - Muse 2
# # 1308 - Muse 2
# # 1311 - Muse 2
# # 1314 - Muse 2
# # 1407 - only session1

# Both 

# Fall 2018
# subs = [101, 102, 103, 104, 106, 108, 109, 110, 111, 112,
#         202, 203, 204, 205, 207, 208, 209, 210, 211, 
#         301, 302, 303, 304, 305, 306, 307, 308, 309,
#         1101, 1102, 1103, 1104, 1105, 1106, 1108, 1109, 1110,
#         1202, 1203, 1205, 1206, 1209, 1210, 1211, 1215,
#         1301, 1302, 1313, 
#         1401, 1402, 1403, 1404, 1405,  1408, 1410, 1411, 1412, 1413, 1413, 1414, 1415, 1416]

###################################################################################################
# Set some settings


# basic numbers
n_subs = len(subs)
n_sesh = 2
conditions = ['valid','invalid']
n_cond = len(conditions)

# cutoff trials that are too slow or fast
rt_toofast = 250
rt_tooslow = 1500

#creates arrays to save output
count_rt = np.zeros((n_subs, n_sesh, n_cond))
median_rt = np.zeros((n_subs, n_sesh, n_cond))
prop_accu = np.zeros((n_subs, n_sesh, n_cond))


###################################################################################################
# Single Subject example

#select single subject
sub = subs[0]
print('Subject - ' + str(sub))

#just one session 
sesh = 1

#load file
#path =  './subject' + str(sub) + '/session' + str(sesh) + '/'
path =  cueing_data_path + '/muse2016/subject' + str('%04.f' %sub) + '/session' + str('%03.f' %(sesh+1)) + '/'
file =  [x for x in os.listdir(path) if x.endswith('.mat')][0]
output_dict = sio.loadmat(path + file)
print(path + file)

#pull out important info
output = output_dict['output']
accuracy = output[:,6]
rt = output[:,7]
validity = output[:,3]
print(accuracy,rt,validity)

# median rt on each condition	
print('')
print(rt)
print(rt[validity == 0])
print(rt[(validity == 0) & (rt <= rt_tooslow)])

validRT  	=  np.nanmedian(rt[ (validity == 1) &
                              (rt >= rt_toofast) &
                              (rt <= rt_tooslow)])

print('Valid RT = ' + str(validRT) + ' ms')

InvalidRT =  np.nanmedian(rt[ (validity == 0) &
                              (rt >= rt_toofast) &
                              (rt <= rt_tooslow)]) 

print('Invalid RT = ' + str(InvalidRT) + ' ms')


###################################################################################################
# Loop through subjects

for isub, sub in enumerate(subs):
    print('Subject - ' + str(sub))
    for sesh in range(n_sesh):
        # get the path and file name and load data
        #path =  './subject' + str(sub) + '/session' + str(sesh+1) + '/'
        path =  cueing_data_path + '/muse2016/subject' + str('%04.f' %sub) + '/session' + str('%03.f' %(sesh+1)) + '/'
       
        file =  [x for x in os.listdir(path) if x.endswith('.mat')][0]
        output_dict = sio.loadmat(path + file)

        # pull out important stuff
        output = output_dict['output']
        accuracy = output[:,6]
        rt = output[:,7]
        validity = output[:,3]
  
        # median rt on each condition	
        median_rt[isub,sesh,:] 	= [  np.nanmedian(rt[ (validity == 1) & (rt >= rt_toofast) & (rt <= rt_tooslow)]),
                                     np.nanmedian(rt[ (validity == 0) & (rt >= rt_toofast) & (rt <= rt_tooslow)]) ]
    
        # proportion accurate (number accurate / count)
        prop_accu[isub,sesh,:]  = [ np.sum(accuracy[(validity == 1) & (rt >= rt_toofast) & (rt <= rt_tooslow)]) / 
                                   np.sum((validity == 1) & (rt >= rt_toofast) & (rt <= rt_tooslow)),
                                   np.sum(accuracy[(validity == 0) & (rt >= rt_toofast) & (rt <= rt_tooslow)]) /
                                   np.sum((validity == 0) & (rt >= rt_toofast) & (rt <= rt_tooslow)) ]

    
###################################################################################################
# Average over sessions and print data

# Summary stats and collapse sessions
Out_median_RT = np.squeeze(np.nanmean(median_rt,axis=1))
Out_prop_accu = np.squeeze(np.nanmean(prop_accu,axis=1))

print('Median RT')
print(Out_median_RT)
print('Proportion Accurate')
print(Out_prop_accu)


###################################################################################################
# Plot barplot of results

# bar plot results
plt.figure()
# Accuracy
ax = plt.subplot(211)
plt.bar([0,1], np.nanmean(Out_prop_accu,axis=0), 0.6, yerr = np.nanstd(Out_prop_accu,axis=0)/np.sqrt(n_subs))
plt.ylim(.9,.96)
plt.title('Accuracy')
plt.ylabel('Proportion Correct')
ax.set_xticks([0,1])
ax.set_xticklabels(conditions)
# RT
ax = plt.subplot(212)
plt.bar([0,1], np.nanmean(Out_median_RT,axis=0), 0.6, yerr = np.nanstd(Out_median_RT,axis=0)/np.sqrt(n_subs))
plt.ylim(450,600)
plt.title('Reaction Time')
plt.ylabel('RT (ms)')
plt.xlabel('Condition')
ax.set_xticks([0,1])
ax.set_xticklabels(conditions)
plt.show()

###################################################################################################
# Output spreadsheet

## CSV output
column_dict = {'Participant':subs,
               'AccValid':Out_prop_accu[:,0],
               'AccInvalid':Out_prop_accu[:,1],
               'RTValid':Out_median_RT[:,0],
               'RTInvalid':Out_median_RT[:,1] }
df = pd.DataFrame(column_dict)
print(df)
df.to_csv('375CueingBehPy.csv',index=False)


