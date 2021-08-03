# Seasonal model of Brauner et al. COVID-19 Nonpharmaceutical Interventions Effectiveness

This repository contains one part of the data and code used in the paper [Gavenčiak et al.: *Seasonal variation in SARS-CoV-2 transmission in temperate climates*](https://www.medrxiv.org/content/10.1101/2021.06.10.21258647v1). **Note**: this paper is a preprint and has not yet been peer-reviewed.

This repository contains the seasonal variant of the model of [Brauner et al. *Inferring the effectiveness of government interventions against COVID-19*](https://www.medrxiv.org/content/10.1101/2020.05.28.20116129v2.article-info) and has been forked from [epidemics/COVIDNPIs](https://github.com/epidemics/COVIDNPIs); please see that repo for further information.

For the seasonal variant of the model of [Sharma et al. (2021), *Understanding the effectiveness of government interventions in Europe’s second wave of COVID-19*](https://www.medrxiv.org/content/10.1101/2021.03.25.21254330v1), see the repository [gavento/covid_seasonal_Sharma](https://github.com/gavento/covid_seasonal_Sharma).

# Changelog

* Preprint v1 (tag [`preprint-v1`](https://github.com/gavento/covid_seasonal_Brauner/releases/tag/preprint-v1))
  * Add seasonality model, customized and extended plotters
  * Added filtered temperate Europe data subset has been added as `merged_data/data_final_nov_temperate_europe.csv`.
  * Runners and configs for sensitivity analyses
  * Extended trace storage with [Arviz](https://arviz-devs.github.io/) `netcdf` export and JSON for plotting
    * Plotting code in repository [gavento/covid_seasonal_Sharma](https://github.com/gavento/covid_seasonal_Sharma))
  * Minor updates and fixes

* Preprint v2 (tag [`preprint-v2`](https://github.com/gavento/covid_seasonal_Brauner/releases/tag/preprint-v2))
  * Added mobility sensitivity analysis, data and plotters

# Questions?

Please email Tomáš Gavenčiak (`gavento` at `ucw` dot `cz`) or Mrinank Sharma (`mrinank` at `robots` dot `ac` dot `uk`, only regarding their code) for questions regarding the codebase.
