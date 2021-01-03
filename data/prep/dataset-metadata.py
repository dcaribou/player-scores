"""
Generate datapackage.json for Kaggle Dataset
"""

from frictionless import describe_package

package = describe_package(source="appearances.csv", basepath="data/prep")
package.title = "Football players' statistics from Transfermarkt website"
package.keywords = [
  "football", "players", "stats", "statistics", "data",
  "soccer", "games", "matches"
]
package.id = "davidcariboo/player-scores"
package.description = """
# Football Players' Stats
A collection of football (soccer) players' statistics scraped from the Transfermark website.


The source of this dataset is the Transfermarkt players' [detailed performance page](https://www.transfermarkt.co.uk/diogo-jota/leistungsdatendetails/spieler/340950/saison/2020/verein/0/liga/0/wettbewerb/GB1/pos/0/trainer_id/0/plus/1).


The data pipeline is for this dataset is maintained at [player-scores](https://github.com/dcaribou/player-scores) Github project,
including periodic scraping and updating of this data source.
"""
package.get_resource("appearances").name = "Appearances"

package.to_json("data/prep/dataset-metadata.json")