import argparse
import os
import subprocess
import sys
from datetime import datetime

import arviz as az
import numpy as np
import pymc3 as pm
from epimodel import EpidemiologicalParameters, preprocess_data

from scripts.sensitivity_analysis.utils import *

argparser = argparse.ArgumentParser()
argparser.add_argument("data")
argparser.add_argument("--last_day", help="Brauner data: 2020-05-30")
argparser.add_argument("--output_base")
argparser.add_argument("-n", "--no_log", action="store_true")
add_argparse_arguments(argparser)
# Other args of note: 
# --model_build_arg_seasonality_peak_index=1

def main():
    args, extras = argparser.parse_known_args()

    if not args.output_base:
        ts_str = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        args.output_base = (
            f"runs/{args.exp_tag}_{args.model_type}_{ts_str}_pid{os.getpid()}"
        )

    log_output = f"{args.output_base}.log"
    text_output = f"{args.output_base}.txt"
    full_output = f"{args.output_base}.netcdf"
    if not args.no_log:
        print(f"Logging to {log_output}")
        logprocess = subprocess.Popen(
            ["/usr/bin/tee", log_output], stdin=subprocess.PIPE,
        )
        os.close(sys.stdout.fileno())
        os.dup2(logprocess.stdin.fileno(), sys.stdout.fileno())
        os.close(sys.stderr.fileno())
        os.dup2(logprocess.stdin.fileno(), sys.stderr.fileno())

    print(f"CMD: {' '.join(sys.argv)}")

    if args.last_day:
        data = preprocess_data(args.data, last_day=args.last_day)
    else:
        data = preprocess_data(args.data)
    print(f"\nData loaded from {args.data}:")
    print(f"NPI CMs ({len(data.CMs)}): {data.CMs}")
    print(f"Regions ({len(data.Rs)}): {data.Rs}")
    print(f"Days ({len(data.Ds)}): {data.Ds[0]} .. {data.Ds[-1]}")

    ep = EpidemiologicalParameters()

    model_class = get_model_class_from_str(args.model_type)
    bd = {**ep.get_model_build_dict(), **parse_extra_model_args(extras)}
    print(f"\nBD = {bd}")

    print("\nBuilding model ...")
    with model_class(data) as model:
        model.build_model(**bd)

    print("Running inference ...")
    with model.model:
        model.trace = pm.sample(
            args.n_samples,
            tune=min(500, args.n_samples),
            chains=args.n_chains,
            cores=args.n_chains,
            max_treedepth=14,
            target_accept=0.96,
            init="adapt_diag",
        )

    print("Saving as arviz ...")
    with model.model:
#        prior = pm.sample_prior_predictive()
        posterior_predictive = pm.sample_posterior_predictive(model.trace)
        pm_data = az.from_pymc3(
            trace=model.trace,
#            prior=prior,
            posterior_predictive=posterior_predictive,
            coords={"R": data.Rs, "D": data.Ds, "CM": data.CMs},
            dims={"CM_Alpha": ["CM"], "RegionR_noise": ["R"]},
        )
        pm_data.to_netcdf(full_output)


if __name__ == "__main__":
    main()
