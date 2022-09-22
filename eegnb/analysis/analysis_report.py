

# Generating html using Python

from airium import Airium
from typing import Dict
import os
a = Airium()


def get_html(experimental_parameters: Dict):

    eeg_device, experiment, subject, session, example, drop_percentage = experimental_parameters.values()
    #experiment_text = ""
    #with open('experiment_descriptions/{}.txt'.format(experiment), 'r') as f:
     #   experiment_text = f.readlines()

    a('<!DOCTYPE html>')
    with a.html():
        with a.head():
            a.link(href=os.getcwd()+"\\styling.css", rel='stylesheet', type="text/css")
            a.title(_t="Analysis Report")

        with a.body():

            # Navigation bar
            with a.div(klass="topnav"):
                a.a(_t="Description", href="#Description")
                a.a(_t="Raw Epoch", href="#Raw Epoch")
                a.a(_t="Stimulus Response", href="#Stimulus Response")
                a.a(_t="About", href="#about")
            
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
                a.img(src="power_spectrum.png", alt="Raw Epoch")
            
            # Stimulus Response
            with a.div(id="Stimulus Response"):
                a.h2(_t="Stimulus Response")
                with a.p():
                    a("The stimulus response is shown below. The stimulus response is the data that is recorded from the EEG headset after removing noise and artifacts.")
                a.img(src="erp_plot.png", alt="Stimulus Response")

    # Delete saved pictures
    os.remove("power_spectrum.png")
    os.remove("erp_plot.png")

    return str(a)
