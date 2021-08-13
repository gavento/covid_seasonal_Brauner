# Seasonal model of Brauner et al. COVID-19 Nonpharmaceutical Interventions Effectiveness

This repository contains one part of the data and code used in the paper [Gavenčiak et al.: *Seasonal variation in SARS-CoV-2 transmission in temperate climates*](https://www.medrxiv.org/content/10.1101/2021.06.10.21258647v1). **Note: this paper is a preprint and has not yet been peer-reviewed.**

This repository contains the seasonal variant of the model of [Brauner et al. *Inferring the effectiveness of government interventions against COVID-19*](https://www.medrxiv.org/content/10.1101/2020.05.28.20116129v2.article-info) and has been forked from [epidemics/COVIDNPIs](https://github.com/epidemics/COVIDNPIs); please see that repo for further information.

For the seasonal variant of the model of [Sharma et al. (2021), *Understanding the effectiveness of government interventions in Europe’s second wave of COVID-19*](https://www.medrxiv.org/content/10.1101/2021.03.25.21254330v1), see the repository [gavento/covid_seasonal_Sharma](https://github.com/gavento/covid_seasonal_Sharma).

## Data

The main data files used in the model are `data/modelBrauner_dataBrauner.csv` and `data/modelBrauner_dataBrauner.csv` which are derived from `data/data_final_nov_temperate_europe.csv` from Brauner et al. except for number formatting, leaving out unused features and limiting to temperate Europe for `*BraunerTE*` (see the paper for details).

The data files `data/modelBrauner_dataBraunerTE_mobility_*.csv` are enriched with [Google community mobility reports](https://www.google.com/covid19/mobility/). The column `Mobility decrease` is a mean of indicated mobility categories remapped to range from 0.0 (no mobility) to 1.0 (pre-pandemic mobility), as described in the paper.

## Running the model

Instructions for a recent linux distribution (E.g. Ubuntu 20.04+)

* Install poetry in case you don't already have it (follow instructions at https://python-poetry.org for non-default install).

```sh
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - --version 1.1.6
source $HOME/.poetry/env
```

* Install dependencies into a poetry virtualenv

```sh
poetry install
```

* Run all or selected the inferences

Adjust the number of parralel runs: each paralllel run uses 4-8 CPU cores.

```sh
poetry run python scripts/sensitivity_dispatcher.py --max_processes 4 \
  --categories default_Brauner default_BraunerTE basic_R_normal_Brauner basic_R_normal_BraunerTE \
  seasonality_basic_R_normal_BraunerTE seasonality_maxRday_normal_BraunerTE seasonality_maxRday_fixed_BraunerTE \
  seasonality_mobility_1 
```

* To plot the results, use the notebooks from `notebooks/final_results` in the repository [gavento/covid_seasonal_Sharma](https://github.com/gavento/covid_seasonal_Sharma) (move the resulting data in `sensitivity_analysis/` there).

## Changelog

* Preprint v1 (tag [`preprint-v1`](https://github.com/gavento/covid_seasonal_Brauner/releases/tag/preprint-v1))
  * Add seasonality model, customized and extended plotters
  * Added filtered temperate Europe data subset has been added as `merged_data/data_final_nov_temperate_europe.csv`.
  * Runners and configs for sensitivity analyses
  * Extended trace storage with [Arviz](https://arviz-devs.github.io/) `netcdf` export and JSON for plotting
    * Plotting code in repository [gavento/covid_seasonal_Sharma](https://github.com/gavento/covid_seasonal_Sharma))
  * Minor updates and fixes

* Preprint v2 (tag [`preprint-v2`](https://github.com/gavento/covid_seasonal_Brauner/releases/tag/preprint-v2))
  * Added mobility sensitivity analysis, data and plotters
  * Added data files exactly as used
  * Updated configs and readme for easier reproduction

# Questions?

Please email Tomáš Gavenčiak (`gavento` at `ucw` dot `cz`) or Mrinank Sharma (`mrinank` at `robots` dot `ac` dot `uk`, only regarding their code) for questions regarding the codebase.
