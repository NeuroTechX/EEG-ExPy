
# Generating html using Python

from airium import Airium
from typing import Dict
import os
import eegnb
import base64

a = Airium()

    
def get_img_string(image_save_path):
    """ Returns image as string to embed into the html report """
    return base64.b64encode(open(image_save_path, "rb").read()).decode()

def get_html(experimental_parameters: Dict):

    css_path = os.path.join(os.path.dirname(eegnb.__file__), "analysis", "styling.css")
    eeg_device, experiment, subject, session, example, drop_percentage = experimental_parameters.values()
    
    image_save_path = os.path.join(os.path.dirname(eegnb.__file__), "analysis")
    erp_image_path = image_save_path + "\\erp_plot.png"
    pos_image_path = image_save_path + "\\power_spectrum.png"   
    
    """ Possibility of unique experiment text - decision to be made """
    #experiment_text = ""
    #with open('experiment_descriptions/{}.txt'.format(experiment), 'r') as f:
     #   experiment_text = f.readlines()

    a('<!DOCTYPE html>')
    with a.html():
        with a.head():
            a.link(href=css_path, rel='stylesheet', type="text/css")
            a.title(_t="Analysis Report")

        with a.body():

            # Navigation bar
            with a.div(klass="topnav"):
                a.a(_t="Description", href="#Description")
                a.a(_t="Raw Epoch", href="#Raw Epoch")
                a.a(_t="Stimulus Response", href="#Stimulus Response")
            
            # Description
            with a.div(id="Description"):
                a.h1(_t="Analysis Report")
                with a.p():
                    a("Experiment Name: {} <br>".format(experiment))
                    
                    if example:
                        a("Example File <br>")
                    else:
                        a("Subject Id: {} <br>".format(subject))
                        a("Session Id: {} <br>".format(session))
                    
                    a("EEG Device: {} <br>".format(eeg_device))
                    a("Drop Percentage: {} %<br> <br>".format(round(drop_percentage,2)))
                    a('This is an analysis report for the experiment. <br> For more information about the experiment, please visit the <a href="https://neurotechx.github.io/eeg-notebooks/">documentation</a>')
                    #a(experiment_text)
            
            # Raw Epoch
            with a.div(id="Raw Epoch"):
                a.h2(_t="Raw Epoch")
                with a.p():
                    a("The raw epoch is shown below. The raw epoch is the data that is recorded from the EEG headset. The raw epoch is then processed to remove noise and artifacts.")
                a.img(src="data:image/png;base64, {}".format(get_img_string(pos_image_path)), alt="Raw Epoch")
            
            # Stimulus Response
            with a.div(id="Stimulus Response"):
                a.h2(_t="Stimulus Response")
                with a.p():
                    a("The stimulus response is shown below. The stimulus response is the data that is recorded from the EEG headset after removing noise and artifacts.")
                a.img(src="data:image/png;base64, {}".format(get_img_string(erp_image_path)), alt="Stimulus Response")

    # Delete the images
    os.remove(erp_image_path)
    os.remove(pos_image_path)

    # Return the html
    return str(a)
