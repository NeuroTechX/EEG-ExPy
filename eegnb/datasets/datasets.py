

"""
eeg-notebooks dataset fetchers
"""

import os,sys,glob



def fetch_dataset(data_dir=None, experiment=None, site='eegnb_examples', 
                  device='muse2016', subjects='all', sessions='all', load_mne = False):

        """
        
        Return a long-form filenames list and a table saying what 
        subject and session, and run each entry corresponds to 

        Usage:
                data_dir = '/my_folder'
                experiment = 'visual-N170'
                subjects = [1]
                sessions = 'all'
                
                visn170_fnames = fetch_dataset(data_dir=data_dir, subjects='all', experiment='visual-N170',
                site='eegnb_examples')
                
                visnP300_fnames = fetch_dataset(data_dir=data_dir, subjects=[1], experiment='visual-P300',
                site='eegnb_examples')
                


        """;
        
        
    
        experiments_list = ['rest', 'auditory-P300', 'auditory-SSAEP', 'visual-cueing',
                          'visual-gonogo','visual-leftright','visual-N170',
                          'visual-P300','visual-spatialfreq', 'visual-SSVEP']
        
        gdrive_locs = {'visual-SSVEP':'1zj9Wx-YEMJo7GugUUu7Sshcybfsr-Fze',
                        'visual-spatialfreq':'1ggBt7CNvMgddxji-FvxcZoP-IF-PmESX',
                        'visual-P300':'1OLcj-zSjqdNrsBSUAsGBXOwWDnGWTVFC',
                        'visual-N170': '1oStfxzEqf36R5d-2Auyw4DLnPj9E_FAH',
                        'visual-leftright': '1f8A4Vbz0xjfgGIYFldMZ7ZL02x7T0jSt',
                        'visual-nogono': '1C8WKg9TXyp8A3QJ6T8zbGnk6jFcMutad',
                        'visual-cueing': '1ABOVJ9S0BeJOsqdGFnexaTFZ-ZcsIXfQ',
                        'auditory-SSAEP': '1fd0OAyNGWWOHD8e1FnEOLeQMeEoxqEpO',
                        'auditory-P300': '1OEtrRfMOkzDssGv-2Lj56FsArmPnQ2vD'}
        
        wget_str_tpl = r"wget --no-check-certificate 'https://drive.google.com/uc?export=download&id=FILEID' -O OUTFILE"

        # Large files need a modified download commant
        large_downloads = ['visual-cueing']

        wget_str_tpl_ld = r"""wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=FILEID' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=FILEID" -O OUTFILE && rm -rf /tmp/cookies.txt"""

        if experiment not in experiments_list: raise ValueError('experiment not in database')


        download_it = False
        exp_dir = os.path.join(data_dir, experiment, site, device)
        
        if not os.path.isdir(exp_dir): download_it = True

        if download_it:

            if not os.path.isdir(data_dir): os.makedirs(data_dir)

            cwd = os.getcwd()
            code = gdrive_locs[experiment]
            outfile = '%s/%s' %(data_dir, experiment + '.zip')

            if experiment in large_downloads:
              wget_str = wget_str_tpl_ld.replace('FILEID', code).replace('OUTFILE', outfile)
            else:
              wget_str = wget_str_tpl.replace('FILEID', code).replace('OUTFILE', outfile)
            
            print('downloading zip file: for %s' %experiment)
            print(wget_str)
            os.system(wget_str)
            
            os.chdir(data_dir)
            os.system('unzip %s' %outfile)
            
            os.chdir(cwd)
            
           
        
        if subjects == 'all': subjects = ['*']
        if sessions == 'all':  sessions = ['*']
       

        fnames = []
        for subject_nb in subjects:
            if subject_nb is not '*':
                # Format to get 4 digit number, e.g. 0004
                subject_nb = float(subject_nb)
                subject_nb = '%03.f' %subject_nb
                for session_nb in sessions:
                    # Formt to get 3 digit number, e.g. 003
                    if session_nb is not '*':
                        session_nb = float(session_nb)
                        session_nb = '%02.f' %session_nb

                        pth = '{}/subject{}/session{}/*.csv'.format(exp_dir,subject_nb, session_nb)
                        fpaths = glob.glob(pth)
                        fnames += fpaths

        return fnames

