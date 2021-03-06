# :soccer: player-scores
Use data from [trasfermarkt-scraper](https://github.com/dcaribou/transfermarkt-scraper) to compute player's scores and forecast performance. Use forecasts to improve decision-making when creating line-ups for games such as [Fantasy Football](https://fantasy.premierleague.com/), [Biwenger](https://www.biwenger.com/), etc. 

This is an **ongoing project**, that aims to achieve this goal incrementally by

1. Building a clean, public dataset of player appearances' statistics &#8594; [`dataset-improvements`](https://github.com/dcaribou/player-scores/issues?q=is%3Aissue+is%3Aopen+label%3A%22dataset+improvements%22)
2. Training a machine learning model that uses historical data to forecast player's performance on their next game &#8594; [`machine-learning`](https://github.com/dcaribou/player-scores/issues?q=is%3Aissue+is%3Aopen+label%3A%22machine+learning%22)
3. Create a line-up analysis tool by displaying forecasts on a dashboard &#8594; [`visualization`](https://github.com/dcaribou/player-scores/issues?q=is%3Aissue+is%3Aopen+label%3Avisualizations)

## [data](data)
All project data assets are kept inside the `data` folder. This is a [DVC](https://dvc.org/) repository, therefore all files for the current revision can be pulled from remote storage with `dvc pull`.

## [prep](prep)
Scripts for transforming raw scraped data into a cleaned and validated dataset that can be published as a [data package](https://specs.frictionlessdata.io/) are in the `prep` folder. Prepared assets are used as the base of further analysis in this project.

Checkout [our Kaggle Dataset](https://www.kaggle.com/davidcariboo/player-scores) for a reference of prepared files produced in this step.

## [viz](viz) 🚧
Some [custom visualizations](https://public.tableau.com/views/Dashboard_16101859073170/OffensivePerformance?:language=es&:display_count=y&publish=yes&:origin=viz_share_link) built on top of appearances for demonstrative purposes.

## [infra](infra)
Define all the necessary infrastructure for the project in the AWS cloud.

