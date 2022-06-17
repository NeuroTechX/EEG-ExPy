""" 
Initial run of the Experiment Class Refactor base class

Derived classes have to set a few things in major:
1. load_stimulus function : returns an array of stimuli
2. present_stimulus function : presents the stimuli and pushes eeg data back and forth as needed
Additional parameters can be set from the derived class as per the initializer

"""

class Experiment:

    def __init_(self, exp_name):
        """ Anything that must be passed as a minimum for the experiment should be initialized here """
        
        """ Dk if this overwrites the class variable or is worth doing 
        if we just assume they will overwrite """
        
        self.exp_name= exp_name
        self.instruction_text = """\nWelcome to the {} experiment!\nStay still, focus on the centre of the screen, and try not to blink. \nThis block will run for %s seconds.\n
        Press spacebar to continue. \n""".format(exp_name) 
        self.duration=120 
        self.eeg:EEG=None 
        self.save_fn=None 
        self.n_trials=2010
        self.iti = 0.4
        self.soa = 0.3
        self.jitter = 0.2
    
    def setup(self):

        self.record_duration = np.float32(self.duration)
        self.markernames = [1, 2]
        
        # Setup Trial list -> Common in most (csv in Unicorn)
        self.parameter = np.random.binomial(1, 0.5, n_trials)
        self.trials = DataFrame(dict(parameter=parameter, timestamp=np.zeros(n_trials)))

        # Setup Graphics 
        mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True) 
        
        # Needs to be overwritten by specific experiment
        self.stim = self.load_stimulus()
        
        # Show Instruction Screen
        self.show_instructions(duration=duration)

        # Establish save function
        if self.save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            random_id = random.randint(1000,10000)
            self.save_fn = generate_save_fn(eeg.device_name, experiement_id, random_id, random_id, "unnamed")
            print(
                f"No path for a save file was passed to the experiment. Saving data to {save_fn}"
            )
                
    def present(self):
        """ Do the present operation for a bunch of experiments """
    
        # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
        if eeg:
            eeg.start(self.save_fn, duration=self.record_duration + 5)

        start = time()
        
        # Iterate through the events
        for ii, trial in self.trials.iterrows():
          
            # Intertrial interval
            core.wait(self.iti + np.random.rand() * self.jitter)

            # Some form of presenting the stimulus - sometimes order changed in lower files like ssvep
            self.present_stimulus(self.trials, ii, self.eeg, self.markernames)

            # Offset
            mywin.flip()
            if len(event.getKeys()) > 0 or (time() - start) > self.record_duration:
                break
            event.clearEvents()

        # Close the EEG stream 
        if eeg:
            eeg.stop()

    
    def show_instructions(self):
    
        self.instruction_text = self.instruction_text % duration

        # graphics
        mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True)
        mywin.mouseVisible = False

        # Instructions
        text = visual.TextStim(win=mywin, text=self.instruction_text, color=[-1, -1, -1])
        text.draw()
        mywin.flip()
        event.waitKeys(keyList="space")

        mywin.mouseVisible = True
        mywin.close()