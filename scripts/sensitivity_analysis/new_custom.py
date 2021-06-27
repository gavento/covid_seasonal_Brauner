import argparse
import json
import lzma
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import arviz as az
import numpy as np
import pymc3 as pm
import threadpoolctl
from epimodel import EpidemiologicalParameters, preprocess_data
from scripts.sensitivity_analysis.utils import *

argparser = argparse.ArgumentParser()
argparser.add_argument("--data", default="")
argparser.add_argument("--last_day", help="Brauner data: 2020-05-30")
argparser.add_argument("-n", "--no_log", action="store_true")
argparser.add_argument("-P", "--force_progress", action="store_true")
argparser.add_argument("--target_accept", default=0.96, type=float)
argparser.add_argument(
    "--model_config_name",
    help="Model configuration tag. HACK: used for data identification",
    default="default",
)
argparser.add_argument(
    "--output_base",
    dest="output_base",
    type=str,
    help="Override destination path prefix (adding '.log', '_summary.json', '_full.netcdf')",
    default="",
)

argparser.add_argument(
    "--basic_R_mean",
    dest="basic_R_mean",
    type=float,
    default=3.28,
    help="Basic R mean (default 3.28, 1.35 for Sharma et al.)",
)

argparser.add_argument(
    "--max_R_day_prior",
    dest="max_R_day_prior",
    type=str,
    default="fixed",
    help="Prior for the day of the seasonally-highest R ('fixed', 'normal')",
)
argparser.add_argument(
    "--max_R_day",
    dest="max_R_day",
    type=float,
    default=1.0,
    help="Day of the seasonally-highest R (1..365, default 1 = Jan 1)",
)
argparser.add_argument(
    "--max_R_day_scale",
    dest="max_R_day_scale",
    type=float,
    default=42.0,
    help="Scale for for the day of the seasonally-highest R (mean is 1 = Jan 1)",
)
add_argparse_arguments(argparser)
# Other args of note:
# --model_build_arg_seasonality_peak_index=1


def load_keys_from_samples(keymap, posterior_samples, summary_dict):
    for k, v in keymap.items():
        if k in posterior_samples:
            # save to list
            a = np.asarray(posterior_samples[k])
            summary_dict[v] = a.reshape(-1, *a.shape[2:]).tolist()
    return summary_dict


def main():
    args, extras = argparser.parse_known_args()

    if not args.output_base:
        ts_str = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        args.output_base = (
            f"sensitivity_analysis/{args.model_config_name}/{args.exp_tag}/{args.model_type}_{ts_str}_pid{os.getpid()}"
        )
    Path(args.output_base).parent.mkdir(parents=True, exist_ok=True)

    log_output = f"{args.output_base}.log"
    full_output = f"{args.output_base}_full.netcdf"
    summary_output = f"{args.output_base}_summary.json"
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

    if args.max_R_day_prior == "fixed":
        max_R_day_prior = {
            "type": "fixed",
            "value": float(args.max_R_day),
        }
    elif args.max_R_day_prior == "normal":
        max_R_day_prior = {
            "type": "normal",
            "mean": 1.0,
            "scale": float(args.max_R_day_scale),
        }
    else:
        raise Exception("Invalid seasonality_max_R_day_prior")

    bd = {
        **ep.get_model_build_dict(),
        **parse_extra_model_args(extras),
    }
    bd["max_R_day_prior"] = max_R_day_prior
    bd["basic_R_prior"] = {
        "type": "trunc_normal",
        "mean": args.basic_R_mean,
    }  ## Note: Used only in output
    bd["R_prior_mean"] = args.basic_R_mean
    print(f"\nBD = {bd}")

    start = time.time()
    print("\nBuilding model ...")
    with model_class(data) as model:
        model.build_model(**bd)

    print("Running inference ...\n")
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
    end = time.time()

    print("\n\nSaving as arviz ...")
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

    print("\n\nSaving as json ...")

    if args.n_samples >= 4 and args.n_chains >= 2:
        all_rhat = np.concatenate(
            [v.values.ravel() for v in az.rhat(pm_data.posterior).data_vars.values()]
        )
        print(f"  {np.sum(np.isnan(all_rhat))} Rhat were nan")
        all_rhat = all_rhat[np.logical_not(np.isnan(all_rhat))]
        rhat = {
                "med": float(np.percentile(all_rhat, 50)),
                "upper": float(np.percentile(all_rhat, 97.5)),
                "lower": float(np.percentile(all_rhat, 2.5)),
                "max": float(np.max(all_rhat)),
                "min": float(np.min(all_rhat)),
            }
    else:
        rhat = None

    info_dict = dict(
        model_name=str(model_class.__name__),
        model_config_name=args.model_config_name,
        divergences=model.trace["diverging"].nonzero()[0].size,
        time_per_sample=float(end - start) / args.n_samples,
        total_runtime=float(end - start),
        rhat=rhat,
        data_path=args.data,
        cm_names=model.d.CMs,
        exp_tag=args.exp_tag,
        exp_config=bd,
        model_kwargs=bd,
    )
    load_keys_from_samples(
        {
            "seasonality_beta1": "seasonality_beta1",
            "seasonality_max_R_day": "seasonality_max_R_day",
            "seasonality_local_beta1": "seasonality_local_beta1",
            "CM_Alpha": "alpha_i",
            "MeanRegionR": "mean_region_R",
        },
        pm_data.posterior,
        info_dict,
    )
    with open(summary_output, "wb") as f:
        f.write(json.dumps(info_dict, ensure_ascii=False, indent=4).encode("utf8"))


if __name__ == "__main__":
    main()
