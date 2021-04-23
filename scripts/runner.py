import argparse
import os
import subprocess
import sys
from datetime import datetime

import arviz as az
import numpy as np
import pymc3 as pm
import threadpoolctl
from epimodel import EpidemiologicalParameters, preprocess_data

from scripts.sensitivity_analysis.utils import *

argparser = argparse.ArgumentParser()
argparser.add_argument("data")
argparser.add_argument("--last_day", help="Brauner data: 2020-05-30")
argparser.add_argument("--output_base")
argparser.add_argument("-n", "--no_log", action="store_true")
argparser.add_argument("-P", "--force_progress", action="store_true")
argparser.add_argument("--target_accept", default=0.96, type=float)
argparser.add_argument(
    "--seasonality_peak_index",
    type=int,
    default=0,
    help="Day of 'maximal seasonal R' relative to data start (!) (only used in seasonal model)",
)
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

    if args.force_progress:
        import fastprogress

        fastprogress.fastprogress.printing = lambda: True
        fastprogress.fastprogress.ProgressBar.update_every = 5.0
        fastprogress.fastprogress.ProgressBar.first_its = 100

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
    bd = {
        "seasonality_peak_index": args.seasonality_peak_index,
        **ep.get_model_build_dict(),
        **parse_extra_model_args(extras),
    }
    print(f"\nBD = {bd}")

    print("\nBuilding model ...")
    with model_class(data) as model:
        model.build_model(**bd)

    print("Running inference ...")
    with threadpoolctl.threadpool_limits(limits=1):
        with model.model:
            model.trace = pm.sample(
                args.n_samples,
                tune=min(500, args.n_samples),
                chains=args.n_chains,
                cores=args.n_chains,
                max_treedepth=14,
                target_accept=args.target_accept,
                init="adapt_diag",
            )

    print("Saving as arviz ...")
    with model.model:
        try:
            prior = pm.sample_prior_predictive()
        except:
            prior = None
        try:
            posterior_predictive = pm.sample_posterior_predictive(model.trace)
        except:
            posterior_predictive = None
        pm_data = az.from_pymc3(
            trace=model.trace,
            prior=prior,
            posterior_predictive=posterior_predictive,
            coords={"R": data.Rs, "D": data.Ds, "CM": data.CMs},
            dims={"CM_Alpha": ["CM"], "RegionR_noise": ["R"]},
        )
        pm_data.to_netcdf(full_output)


if __name__ == "__main__":
    main()
