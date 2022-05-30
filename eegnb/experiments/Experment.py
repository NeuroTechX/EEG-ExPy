


class Experiment:

    def __init_():


    def present(duration=120, eeg: EEG=None, save_fn=None, n_trials=2010, exp_name=""):
        """ Do the present operation for a bunch of experiments """
      
        # Setup Trial list -> Common in most
        parameter = np.random.binomial(1, 0.5, n_trials)
        trials = DataFrame(dict(parameter=parameter, timestamp=np.zeros(n_trials)))

        # Setup Graphics 
        mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True) 
        """ Does specific thing within Experiment Type to load stimulus data """

        # Show Instruction Screen
        show_instructions(duration=duration)

        # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
        if eeg:
        if save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            random_id = random.randint(1000,10000)
            save_fn = generate_save_fn(eeg.device_name, "visual_n170", random_id, random_id, "unnamed")
            print(
                f"No path for a save file was passed to the experiment. Saving data to {save_fn}"
            )
        eeg.start(save_fn, duration=record_duration + 5)

        start = time()
        
        # Iterate through the events
        for ii, trial in trials.iterrows():
          
            # Intertrial interval
            core.wait(iti + np.random.rand() * jitter)

            # Some form of presenting the stimulus - sometimes order changed in lower files like ssvep

            # Push sample
            if eeg:
                timestamp = time()
                if eeg.backend == "muselsl":
                    marker = [markernames[label]]
                else:
                    marker = markernames[label]
                eeg.push_sample(marker=marker, timestamp=timestamp)

            # Offset
            mywin.flip()
            if len(event.getKeys()) > 0 or (time() - start) > record_duration:
                break
            event.clearEvents()


        # Close the EEG stream 
        if eeg:
            eeg.stop()

    def show_instructions(instruction_text):
    
        instruction_text = instruction_text % duration

        # graphics
        mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True)

        mywin.mouseVisible = False

        # Instructions
        text = visual.TextStim(win=mywin, text=instruction_text, color=[-1, -1, -1])
        text.draw()
        mywin.flip()
        event.waitKeys(keyList="space")

        mywin.mouseVisible = True
        mywin.close()