

from eegnb.analysis.pipelines import analysis_report, load_data
analysis_report( subject=1,session=1, eegdevice='muse2016_bfn', experiment='visual-N170', site='eegnb_examples')


load_data( subject_id=1,session_nb=1, device_name='muse2016_bfn', experiment='visual-N170', site='eegnb_examples', data_dir='~/.eegnb/data')


same as analysis prompt with 

example and non-example (specifiyng all above args upon cli prompt)
