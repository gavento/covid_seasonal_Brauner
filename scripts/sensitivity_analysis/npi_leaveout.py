"""
:code:`npi_leaveout.py`

Leave our specified NPIs. Useful to study the sensitivity of the results to the inclusion of particular NPIs.
"""

import pymc3 as pm

from epimodel import EpidemiologicalParameters
from epimodel.preprocessing.data_preprocessor import preprocess_data

import argparse

from scripts.sensitivity_analysis.utils import *

argparser = argparse.ArgumentParser()
argparser.add_argument('--npis', nargs='+', dest='npis', type=int)
add_argparse_arguments(argparser)

if __name__ == '__main__':

    args, extras = argparser.parse_known_args()

    data = preprocess_data(get_data_path(), last_day='2020-05-30')
    data.mask_reopenings()

    output_string = ''
    for npi_index in args.npis:
        data.ActiveCMs[:, npi_index, :] = 0
        output_string = f'{output_string}{npi_index}'
    output_string = f'{output_string}.txt'

    ep = EpidemiologicalParameters()
    model_class = get_model_class_from_str(args.model_type)

    bd = {**ep.get_model_build_dict(), **parse_extra_model_args(extras)}

    with model_class(data) as model:
        model.build_model(**bd)

    with model.model:
        model.trace = pm.sample(args.n_samples, tune=500, chains=args.n_chains, cores=args.n_chains, max_treedepth=14,
                                target_accept=0.96, init='adapt_diag')

    save_cm_trace(output_string, model.trace.CMReduction, args.exp_tag,
                  generate_base_output_dir(args.model_type, parse_extra_model_args(extras)))

    if model.country_specific_effects:
        output_string = output_string.replace('.txt', '-cs.txt')
        nS, nCMs = model.trace.CMReduction.shape
        full_trace = np.exp(
            np.log(model.trace.CMReduction) + np.random.normal(size=(nS, nCMs)) * model.trace.CMAlphaScales)
        save_cm_trace(output_string, full_trace, args.exp_tag,
                      generate_base_output_dir(args.model_type, parse_extra_model_args(extras)))
