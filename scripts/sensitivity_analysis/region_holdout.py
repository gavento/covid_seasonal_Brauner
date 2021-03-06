"""
:code:`region_holdout.py`

Hold out data for a specified region. Useful for exploring how well the model predicts the infection course in held-out data.
"""

import pymc3 as pm

from epimodel import EpidemiologicalParameters
from epimodel.preprocessing.data_preprocessor import preprocess_data

import argparse
import pickle

from scripts.sensitivity_analysis.utils import *

import os

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

argparser = argparse.ArgumentParser()
argparser.add_argument('--rg', dest='rg', type=str, help='Region to leave out - alpha 2 code')
add_argparse_arguments(argparser)

if __name__ == '__main__':
    args, extras = argparser.parse_known_args()


    class ResultsObject():
        def __init__(self, indx, trace):
            self.CMReduction = trace.CMReduction
            self.RegionR = trace.RegionR[:, indx]

            try:
                self.InfectedCases = trace.InfectedCases[:, indx, :]
                self.ExpectedCases = trace.ExpectedCases[:, indx, :]
                self.PsiCases = trace.PsiCases
                self.InitialSizeCases_log = trace.InitialSizeCases_log[:, indx]
            except:
                pass

            try:
                self.InfectedDeaths = trace.InfectedDeaths[:, indx, :]
                self.ExpectedDeaths = trace.ExpectedDeaths[:, indx, :]
                self.PsiDeaths = trace.PsiDeaths
                self.InitialSizeDeaths_log = trace.InitialSizeDeaths_log[:, indx]
            except:
                pass

            try:
                self.GrowthCasesNoise = trace.GrowthCasesNoise[:, indx, :]
                self.GrowthDeathsNoise = trace.GrowthDeathsNoise[:, indx, :]
            except:
                pass


    data = preprocess_data(get_data_path(), last_day='2020-05-30')
    data.mask_reopenings()

    if 'deaths_only' in args.model_type:
        data.remove_regions_min_deaths(5)

    data.mask_region(args.rg)
    region_index = data.Rs.index(args.rg)

    ep = EpidemiologicalParameters()
    model_class = get_model_class_from_str(args.model_type)

    bd = {**ep.get_model_build_dict(), **parse_extra_model_args(extras)}
    pprint_mb_dict(bd)

    with model_class(data) as model:
        model.build_model(**bd)

    ta = get_target_accept_from_model_str(args.model_type)

    with model.model:
        model.trace = pm.sample(args.n_samples, tune=500, chains=args.n_chains, cores=args.n_chains, max_treedepth=14,
                                target_accept=ta, init='adapt_diag')

    results_obj = ResultsObject(region_index, model.trace)

    pickle.dump(results_obj, open(
        os.path.join(generate_base_output_dir(args.model_type, parse_extra_model_args(extras)), f'{args.rg}.pkl'),
        'wb'))

    save_cm_trace(f'{args.rg}.txt', model.trace.CMReduction, args.exp_tag,
                  generate_base_output_dir(args.model_type, parse_extra_model_args(extras)))

    if model.country_specific_effects:
        nS, nCMs = model.trace.CMReduction.shape
        full_trace = np.exp(
            np.log(model.trace.CMReduction) + np.random.normal(size=(nS, nCMs)) * model.trace.CMAlphaScales)
        save_cm_trace(f'{args.rg}-cs.txt', full_trace, args.exp_tag,
                      generate_base_output_dir(args.model_type, parse_extra_model_args(extras)))
