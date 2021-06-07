# Seasonal model of Brauner et al. COVID-19 Nonpharmaceutical Interventions Effectiveness

This repository contains the data and code used in the paper [Gavenčiak et al.: *Seasonal variation in SARS-CoV-2 transmission in temperate climates*]().

This repository contains the seasonal variant of the model of [Brauner et al. *Inferring the effectiveness of government interventions against COVID-19*](https://www.medrxiv.org/content/10.1101/2020.05.28.20116129v2.article-info) and has been forked from [epidemics/COVIDNPIs](https://github.com/epidemics/COVIDNPIs); please see that repo for further information.

For the seasonal variant of the model of [Sharma et al. (2021), *Understanding the effectiveness of government interventions in Europe’s second wave of COVID-19*](https://www.medrxiv.org/content/10.1101/2021.03.25.21254330v1), see the repository [gavento/covid_seasonal_Sharma](https://github.com/gavento/covid_seasonal_Sharma).

## Notes

The original code has been extended with a seasonal model `epimodel.pymc3_models.models.ComplexDifferentEffectsWithSeasonalityModel`, extended trace storage with Arviz `netcdf` export and JSON for plotting, and other minor QoL updates. The filtered temperate Europe data subset has been added as `merged_data/data_final_nov_temperate_europe.csv`.

Please contact Tomáš Gavenčiak or Mrinank Sharma for questions regarding the codebase.