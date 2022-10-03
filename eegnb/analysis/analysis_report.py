
# Generating html using Python

from airium import Airium
from typing import Dict
import os
import eegnb
import base64

a = Airium()

def get_experiment_information(experiment:str):
    analysis_save_path = os.path.join(os.path.dirname(eegnb.__file__), "analysis")
    file_path = os.path.join(analysis_save_path, "experiment_descriptions")
    
    with open(os.path.join(file_path, experiment + ".txt"), 'r') as f:
        experiment_text = f.readlines()
    
    return experiment_text

def get_img_string(image_save_path):
    """ Returns image as string to embed into the html report """
    return base64.b64encode(open(image_save_path, "rb").read()).decode()

def get_html(experimental_parameters: Dict):

    # add variable to store the link
    analysis_save_path = os.path.join(os.path.dirname(eegnb.__file__), "analysis")
    css_path = os.path.join(analysis_save_path, "styling.css")
    eeg_device, experiment, subject, session, example, drop_percentage, epochs_chosen = experimental_parameters.values()

    erp_image_path = os.path.join(os.getcwd(), "erp_plot.png")
    pos_image_path = os.path.join(os.getcwd(), "power_spectrum.png")

    experiment_text = get_experiment_information(experiment)
      
    
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
                    a('This is an analysis report for the experiment. <br> For more information about the experiment, please visit the <a href="https://neurotechx.github.io/eeg-notebooks/">documentation</a><br><br>')
                    a("{}<br>".format(experiment_text[0]))
                    a("{}<br>".format(experiment_text[1]))
                    
            # Raw Epoch
            with a.div(id="Raw Epoch"):
                a.h2(_t="Raw Epoch")
                with a.p():
                    a("The power spectrum of the raw epoch is displayed below. The raw epoch is then processed to remove noise and artifacts.")
                a.img(src="data:image/png;base64, {}".format(get_img_string(pos_image_path)), alt="Raw Epoch")
            
            # Stimulus Response
            with a.div(id="Stimulus Response"):
                a.h2(_t="Stimulus Response")
                with a.p():
                    a("The stimulus response is shown below. The stimulus response is the amplitude response at the specific timescales where the response to the stimulus can be detected. <br>")
                    a("Epochs chosen: {} <br>".format(epochs_chosen))
                    a("Drop Percentage: {} %<br> <br>".format(round(drop_percentage,2)))
                a.img(src="data:image/png;base64, {}".format(get_img_string(erp_image_path)), alt="Stimulus Response")

    # Delete the images
    os.remove(erp_image_path)
    os.remove(pos_image_path)

    # Return the html
    return str(a)
