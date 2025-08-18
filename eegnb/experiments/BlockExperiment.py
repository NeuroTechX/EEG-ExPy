"""
BlockExperiment Class - Extends BaseExperiment with block-based functionality

This class provides block-based experiment capabilities by inheriting from BaseExperiment
and overriding the run method to handle multiple blocks. It loads stimulus only once
and reuses it across blocks, while allowing block-specific instructions.

Experiments that need block-based execution should inherit from this class instead of BaseExperiment.
"""
from abc import ABC
from time import time

from .Experiment import BaseExperiment


class BlockExperiment(BaseExperiment, ABC):
    """
    Extended experiment class that inherits from BaseExperiment to provide block-based functionality.
    
    This class is designed for experiments that need to run multiple blocks, with each block
    having its own instructions and duration. It loads stimulus only once and reuses it across blocks.
    """

    def __init__(self, exp_name, block_duration, eeg, save_fn, block_trial_size, n_blocks, iti: float, soa: float, jitter: float,
                 use_vr=False, use_fullscr=True, rift=None):
        """ Initializer for the Block Experiment Class

        Args:
            exp_name (str): Name of the experiment
            block_duration (float): Duration of each block in seconds
            eeg: EEG device object for recording
            save_fn (str): Save filename for data
            block_trial_size (int): Number of trials per block
            n_blocks (int): Number of blocks to run
            iti (float): Inter-trial interval
            soa (float): Stimulus on arrival
            jitter (float): Random delay between stimulus
            use_vr (bool): Use VR for displaying stimulus
            use_fullscr (bool): Use fullscreen mode
        """
        # Calculate total trials for the base class
        total_trials = block_trial_size * n_blocks
        
        # Initialize the base experiment with total trials
        # Pass None for duration if block_duration is None to ignore time spent in instructions
        super().__init__(exp_name, block_duration, eeg, save_fn, total_trials, iti, soa, jitter, use_vr, use_fullscr, rift=rift)
        
        # Store block-specific parameters
        self.block_duration = block_duration
        self.block_trial_size = block_trial_size
        self.n_blocks = n_blocks
        
        # Current block index
        self.current_block_index = 0
        
        # Original save filename
        self.original_save_fn = save_fn
        
        # Flag to track if stimulus has been loaded
        self.stimulus_loaded = False

    def present_block_instructions(self, current_block):
        """
        Display instructions for the current block to the user.
        
        This method is meant to be overridden by child classes to provide
        experiment-specific instructions before each block. The base implementation
        simply flips the window without adding any text.
        
        This method is called by __show_block_instructions in a loop until the user
        provides input to continue or cancel the experiment.
        
        Args:
            current_block (int): The current block number (0-indexed), used to customize
                                instructions for specific blocks if needed.
        """
        self.window.flip()

    def _show_block_instructions(self, block_number):
        """
        Show instructions for a specific block
        
        Args:
            block_number (int): Current block number (0-indexed)
            
        Returns:
            tuple: (continue_experiment, instruction_end_time)
                - continue_experiment (bool): Whether to continue the experiment
        """
        
        # Clear any previous input
        self._clear_user_input()
        
        # Wait for user input to continue
        while True:
            # Display the instruction text
            super()._draw(lambda: self.present_block_instructions(block_number))

            if self._user_input('start'):
                return True
            elif self._user_input('cancel'):
                return False

    def run(self, instructions=True):
        """
        Run the experiment as a series of blocks
        
        This method overrides BaseExperiment.run() to handle multiple blocks.
        
        Args:
            instructions (bool): Whether to show the initial experiment instructions
        """
        # Setup the experiment (creates window, loads stimulus once)
        self.setup(instructions)
        
        # Start EEG Stream once for all blocks
        if self.eeg:
            print("Wait for the EEG-stream to start...")
            self.eeg.start(self.save_fn)
            print("EEG Stream started")
        
        # Run each block
        for block_index in range(self.n_blocks):
            self.current_block_index = block_index
            print(f"Starting block {block_index + 1} of {self.n_blocks}")
            
            # Show block-specific instructions
            if not self._show_block_instructions(block_index):
                break
            
            # Run this block
            if not self._run_trial_loop(start_time=time(), duration=self.block_duration):
                break
        
        # Stop EEG Stream after all blocks
        if self.eeg:
            self.eeg.stop()
            
        # Close window at the end of all blocks
        self.window.close()
