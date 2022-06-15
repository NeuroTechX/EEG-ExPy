""" 
Initial run of the Experiment Class Refactor base class

Specific experiments are implemented as sub classes that inherit a load_stimulus and present_stimulus method
"""

class Experiment:

    def __init_(self, exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter):
        """ Anything that must be passed as a minimum for the experiment should be initialized here """

        self.exp_name = exp_name
        self.instruction_text = """\nWelcome to the {} experiment!\nStay still, focus on the centre of the screen, and try not to blink. \nThis block will run for %s seconds.\n
        Press spacebar to continue. \n""".format(self.exp_name)
        self.duration = duration
        self.eeg = eeg
        self.save_fn = save_fn
        self.n_trials = n_trials
        self.iti = iti
        self.soa = soa
        self.jitter = jitter
    
    def load_stimulus(self):
        """ Needs to be overwritten by specific experiment """
        pass

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
        self.show_instructions()

        # Establish save function
        if self.save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            random_id = random.randint(1000,10000)
            self.save_fn = generate_save_fn(eeg.device_name, experiement_id, random_id, random_id, "unnamed")
            print(
                f"No path for a save file was passed to the experiment. Saving data to {save_fn}"
            )

    def present_stimulus(self):
        """ Needs to be overwritten by specific experiment """
        pass

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
            self.present_stimulus()

            # Offset
            mywin.flip()
            if len(event.getKeys()) > 0 or (time() - start) > self.record_duration:
                break
            event.clearEvents()

        # Close the EEG stream 
        if eeg:
            eeg.stop()

    
    def show_instructions(self):
    
        self.instruction_text = self.instruction_text % self.duration

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