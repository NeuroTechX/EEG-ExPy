

Looking for a general implementation structure where base class implements and passes the following functions, 

def load_stimulus() -> stim (some form of dd array)

def present_stimulus() -> given trial details does specific thing for experiment 

** Slight issue is that a lot of parameters will have to be passed which is not the best in practice

Stuff that can be overwritten in general ...
instruction_text
parameter/trial
