import os
import glob
import shutil
import zipfile

import requests
import gdown

from datetime import datetime
from eegnb import DATA_DIR


# eegnb example data sites. do not select these when zipping recordings
eegnb_sites = ["eegnb_examples", "grifflab_dev", "jadinlab_home"]


def fetch_dataset(
    data_dir=None,
    experiment=None,
    site="eegnb_examples",
    device="muse2016",
    subjects="all",
    sessions="all",
    download_method="gdown",
):
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



    """
    # List of experiments available
    experiments_list = [
        "rest",
        "auditory-P300",
        "auditory-SSAEP",
        "visual-cueing",
        "visual-gonogo",
        "visual-leftright",
        "visual-N170",
        "visual-P300",
        "visual-spatialfreq",
        "visual-SSVEP",
    ]

    # List gdrive extensions for various experiments
    gdrive_locs = {
        "visual-SSVEP": "1zj9Wx-YEMJo7GugUUu7Sshcybfsr-Fze",
        "visual-spatialfreq": "1ggBt7CNvMgddxji-FvxcZoP-IF-PmESX",
        "visual-P300": "1OLcj-zSjqdNrsBSUAsGBXOwWDnGWTVFC",
        "visual-N170": "1oStfxzEqf36R5d-2Auyw4DLnPj9E_FAH",
        "visual-leftright": "1f8A4Vbz0xjfgGIYFldMZ7ZL02x7T0jSt",
        "visual-nogono": "1C8WKg9TXyp8A3QJ6T8zbGnk6jFcMutad",
        "visual-cueing": "1ABOVJ9S0BeJOsqdGFnexaTFZ-ZcsIXfQ",
        "auditory-SSAEP": "1fd0OAyNGWWOHD8e1FnEOLeQMeEoxqEpO",
        "auditory-P300": "1OEtrRfMOkzDssGv-2Lj56FsArmPnQ2vD",
    }

    # If no non-default top-level data path specified, use default
    if data_dir is None:
        data_dir = DATA_DIR

    # check parameter entries
    if experiment not in experiments_list:
        raise ValueError("experiment not in database")

    # check if data has been previously downloaded
    download_it = False
    exp_dir = os.path.join(data_dir, experiment, site, device)
    if not os.path.isdir(exp_dir):
        download_it = True

    if download_it:
        # check if data directory exits. If not, create it
        if os.path.exists(data_dir) is not True:
            os.makedirs(data_dir)

        destination = os.path.join(data_dir, "downloaded_data.zip")

        if download_method == "gdown":
            URL = "https://drive.google.com/uc?id=" + gdrive_locs[experiment]
            gdown.download(URL, destination, quiet=False)
        elif download_method == "requests":
            URL = "https://docs.google.com/uc?export=download"

            session = requests.Session()
            response = session.get(
                URL, params={"id": gdrive_locs[experiment]}, stream=True
            )

            # get the confirmation token to download large files
            token = None
            for key, value in response.cookies.items():
                if key.startswith("download_warning"):
                    token = value

            if token:
                params = {"id": id, "confirm": token}
                response = session.get(URL, params=params, stream=True)

            # save content to the zip-file
            CHUNK_SIZE = 32768
            with open(destination, "wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
        else:
            raise ValueError("download_method not supported")

        # unzip the file
        with zipfile.ZipFile(destination, "r") as zip_ref:
            zip_ref.extractall(data_dir)

        # remove the compressed zip archive
        os.remove(destination)

    if subjects == "all":
        subjects = ["*"]
    if sessions == "all":
        sessions = ["*"]

    # If 'all' subjects and 'all sesssions:
    if (subjects[0] == "*") and (sessions[0] == "*"):
        pth = os.path.join(
            exp_dir, f"subject{subjects[0]}", f"session{sessions[0]}", "*.csv"
        )
        fnames = glob.glob(pth)
    # Else, if specific subjects and sessions
    else:
        fnames = []
        for subject_nb in subjects:
            if subject_nb != "*":
                # Format to get 4 digit number, e.g. 0004
                subject_nb = float(subject_nb)
                subject_nb = "%03.f" % subject_nb
                for session_nb in sessions:
                    # Formt to get 3 digit number, e.g. 003
                    if session_nb != "*":
                        session_nb = float(session_nb)
                        session_nb = "%02.f" % session_nb

                        pth = os.path.join(
                            exp_dir,
                            f"subject{subject_nb}",
                            f"session{session_nb}",
                            "*.csv",
                        )
                        # pth = '{}/subject{}/session{}/*.csv'.format(exp_dir,subject_nb, session_nb)
                        fpaths = glob.glob(pth)
                        fnames += fpaths

    return fnames


def zip_data_folders(experiment: str, site: str = "local"):

    """
    Run data zipping

    Usage

    from eegnb.datasets.datasets import zip_data_folders
    zip_data_folders(experiment='visual-N170')


    See also the command-line program
    eegnb runzip -ip

    """

    if site in eegnb_sites:
        print('Invalid Directory')
        raise ValueError ('{} is one of the eegnb example data sites. Your recordings should not be in that folder.'.format(site))


    print('\nRunning Data Zipper')
    zip_directory=os.path.join(DATA_DIR,experiment,site)
    print('Looking for {} within {} \n'.format(experiment+'/'+site,DATA_DIR))
    
    if not os.path.isdir(zip_directory):
        print('Invalid Directory')
        raise ValueError ('{} directory does not exist'.format(zip_directory))

    print('Files Found! Zipping all files in {} '.format(zip_directory))

    date_time=datetime.now()
    datetime_str=date_time.strftime("%Y-%m-%d-%H-%M")
    output_filename=os.path.join(os.path.expanduser("~/Desktop"),
                                 'eegnb_zipdata__' + experiment+'_site-'+site+'_'+datetime_str)

    shutil.make_archive(output_filename,'zip',zip_directory)
    print('Zip file location is at {}\n '.format(output_filename))

