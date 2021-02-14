import pandas
import numpy
import json
from typing import List
from datetime import datetime, timedelta

def flatten(df: pandas.DataFrame, list_fields: List[str]) -> pandas.DataFrame:

  non_list_fileds = [column for column in df.columns if column not in list_fields]

  df_as_json_lists_string = df.to_json(orient='records')
  df_as_json_lists = json.loads(df_as_json_lists_string)

  return pandas.json_normalize(
    df_as_json_lists,
    list_fields,
    non_list_fileds
  )

def renames(df: pandas.DataFrame, mappings: dict) -> pandas.DataFrame:
  return df.rename(
    columns=mappings,
    errors="raise"
  )

def create_surrogate_key(name: str, columns: List[str], df: pandas.DataFrame) -> pandas.DataFrame:
  games_df = df.drop_duplicates(subset=columns).sort_values(
    by=columns
  )[columns]
  games_df[name] = games_df.index.values + 1
  return df.merge(
    games_df,
    on=columns
  )

def parse_aggregate(series: pandas.Series) -> pandas.DataFrame:
  parsed = series.str.split(":", expand=True)
  cols = ['home_club_goals', 'away_club_goals']
  parsed.columns = cols
  parsed[cols] = parsed[cols].apply(pandas.to_numeric, errors='coerce')
  return parsed

def infer_season(series: pandas.Series) -> pandas.Series:
  def infer_season(date: datetime):
    year = date.year
    month = date.month
    if month >= 8 and month <= 12:
      return year
    if month >= 1 and month <8:
      return year - 1

  return series.apply(infer_season)

def add_new_columns(df: pandas.DataFrame) -> pandas.DataFrame:

  def get_href_part(href, part):
    href_parts = href.split('/')
    return href_parts[part]

  df['for_club_id'] = df['for'].apply(lambda x: get_href_part(x['href'], 4)).astype('int32')
  df['for_club_name'] = df['for'].apply(lambda x: get_href_part(x['href'], 1))

  df['opponent_club_id'] = df['opponent'].apply(lambda x: get_href_part(x['href'], 4)).astype(int)
  df['opponent_club_name'] = df['opponent'].apply(lambda x: get_href_part(x['href'], 1))

  df['home_club_name'] = numpy.where(
    df['venue'] == 'H',
    df['for_club_name'],
    df['opponent_club_name']
  )
  df['home_club_id'] = numpy.where(
    df['venue'] == 'H',
    df['for_club_id'],
    df['opponent_club_id']
  )

  df['away_club_name'] = numpy.where(
    df['venue'] == 'H',
    df['opponent_club_name'],
    df['for_club_name']
  )
  df['away_club_id'] = numpy.where(
    df['venue'] == 'H',
    df['opponent_club_id'],
    df['for_club_id']
  )

  df['player_id'] = df['parent'].apply(lambda x: get_href_part(x['href'], 4)).astype('int32')
  df['player_name'] = df['parent'].apply(lambda x: get_href_part(x['href'], 1))

  df_new = create_surrogate_key('game_id', ['home_club_name', 'date'], df)
  df_new = create_surrogate_key('appearance_id', ['player_id', 'date'], df_new)

  df_new[['home_club_goals', 'away_club_goals']] = parse_aggregate(df_new['result'])
  del df_new['result']

  df_new['season'] = infer_season(df_new['date'])

  return df_new

def improve_columns(df: pandas.DataFrame) -> pandas.DataFrame:

  def cast_metric(metric):
    if len(metric) == 0:
      return 0
    else:
      return int(metric)

  def cast_minutes_played(minutes_played):
    if len(minutes_played) > 0:
      numeric = minutes_played[:-1]
      return int(numeric)
    else:
      return 0

  # recasts
  df['goals'] = df['goals'].apply(cast_metric)
  df['assists'] = df['assists'].apply(cast_metric)
  # df['own_goals'] = df['own_goals'].apply(cast_metric)
  df['date'] = pandas.to_datetime(df['date'])
  df['minutes_played'] = df['minutes_played'].apply(cast_minutes_played)

  # reshape cards columns
  df['yellow_cards'] = (df['yellow_cards'].str.len() > 0).astype('int32') + (df['second_yellow_cards'].str.len() > 0).astype('int32')
  del df['second_yellow_cards']

  df['red_cards'] = (df['red_cards'].str.len() > 0).astype('int32')

  # player position long name
  df['player_position'] = numpy.select(
    [
        df['player_position'] == 'RW', 
        df['player_position'] == 'RB',
        df['player_position'] == 'SW',
        df['player_position'] == 'LM',
        df['player_position'] == 'GK',
        df['player_position'] == 'LB',
        df['player_position'] == 'DM',
        df['player_position'] == 'CB',
        df['player_position'] == 'CF',
        df['player_position'] == 'LW',
        df['player_position'] == 'SS',
        df['player_position'] == 'CM',
        df['player_position'] == 'AM',
        df['player_position'] == 'RM',
    ], 
    [
        'Right Winger', 
        'Right-Back',
        'Sweeper',
        'Left Midfield',
        'Goalkeeper',
        'Left-Back',
        'Defensive Midfield',
        'Center-Back',
        'Center Forward',
        'Left Winger',
        'Second Striker',
        'Center Midfiled',
        'Attacking Midfield',
        'Right Midfield',
    ], 
    default=numpy.NaN
)

  return df

def filter_appearances(df: pandas.DataFrame) -> pandas.DataFrame:
  # get rid of 2017 season data as we only have it partially
  df = df[df['season'] == 2020]

  domestic_competitions = [
    'ES1', 'GB1', 'L1', 'IT1', 'FR1', 'GR1', 'PO1', 'BE1', 'UKR1', 'BE1', 'RU1', 'DK1', 'SC1', 'TR1', 'NL1'
  ]
  df = df[df['competition'].isin(domestic_competitions)]

  del df['type']
  del df['href']
  del df['parent']
  del df['venue']
  del df['for']
  del df['for_club_id']
  del df['opponent']
  del df['opponent_club_id']
  del df['opponent_club_name']

  df = df.drop_duplicates()

  return df

def assert_unique_on_column(df: pandas.DataFrame, columns):
  counts = df.groupby(columns).size().reset_index(name='counts')
  assert len(counts[counts['counts'] > 1]) == 0

def validate(df: pandas.DataFrame, validations):
  failed_validations = 0

  def assert_df_not_empty(df: pandas.DataFrame):
    assert len(df) > 0
  # -----------------------------
  # consistency
  # -----------------------------
  def assert_minutes_played_gt_120(df: pandas.DataFrame):
    appearances_w_mp_gt_90 = len(df[df['minutes_played'] > 120])
    assert appearances_w_mp_gt_90 == 0, appearances_w_mp_gt_90
  def assert_goals_in_range(df: pandas.DataFrame):
    assert len(df[df['goals'] > 90]) == 0
  def assert_assists_in_range(df: pandas.DataFrame):
    assert len(df[~df['assists'].between(0, 4)]) == 0
  def assert_own_goals_in_range(df: pandas.DataFrame):
    assert len(df[~df['own_goals'].between(0, 3)]) == 0
  def assert_yellow_cards_range(df: pandas.DataFrame):
    assert len(df[~df['yellow_cards'].between(0,2)]) == 0
  def assert_red_cards_range(df: pandas.DataFrame):
    assert len(df[~df['red_cards'].between(0,1)]) == 0
  def assert_unique_on_player_and_date(df: pandas.DataFrame):
    assert_unique_on_column(df, ['player_id', 'date'])
  def assert_goals_ne_assists(df: pandas.DataFrame):
    assert (df['goals'] != df['assists']).sum() > 0
  def assert_goals_ne_own_goals(df: pandas.DataFrame):
    assert (df['goals'] != df['own_goals']).sum() > 0
  def assert_yellow_cards_not_constant(df: pandas.DataFrame):
    assert df['yellow_cards'].nunique() != 1
  def assert_red_cards_not_constant(df: pandas.DataFrame):
    assert df['red_cards'].nunique() != 1
  # -----------------------------
  # completeness
  # -----------------------------
  def assert_clubs_per_competition(df: pandas.DataFrame):
    clubs_per_domestic_competition = (
      df.groupby(['season', 'competition'])['player_club_name'].nunique()
    )
    # the number of clubs of the scotish league is 12
    # the number of clubs of the turkish league is 21
    n = (numpy.bitwise_not(clubs_per_domestic_competition.between(12, 21))).sum()
    assert n == 0, n

  def assert_games_per_season_per_club(df: pandas.DataFrame):
    games_per_season_per_club = (
      df.groupby(['season', 'competition', 'player_club_name'])['date'].nunique()
    )
    assert (games_per_season_per_club != 38).sum() == 0

  def assert_appearances_per_match(df: pandas.DataFrame):
    appearances_per_match = (
      df.groupby(['home_club_name', 'away_club_name', 'date'])['appearance_id'].nunique()
    )
    assert (appearances_per_match < 11).sum() == 0

  def assert_appearances_per_club_per_game(df: pandas.DataFrame):
    # allow inconsitencies for recent game match
    df_new = df[df['date'] < (datetime.now() - timedelta(days=2))]
    # similarly, each club must have at least 11 appearances per game
    appearances_per_club_per_game = (
      df_new.groupby(['player_club_name', 'game_id'])['appearance_id'].nunique()
    )
    faulty_games = (appearances_per_club_per_game < 11).sum()
    total_games = df_new['game_id'].nunique()
    assert faulty_games == 0, f"{faulty_games}/{total_games}"

  def assert_appearances_freshness_is_less_than_one_week(df: pandas.DataFrame):
    max_appearance_per_club = (
      df.groupby(['player_club_name'])['date'].max()
    )
    total_clubs = len(max_appearance_per_club)
    stale_clubs = (max_appearance_per_club < (datetime.utcnow() - timedelta(days=7))).sum()
    # if more than 5 clubs are stale, fail validation
    assert stale_clubs/total_clubs < 0.4, f"{stale_clubs}/{total_clubs}"

  validations_base = {
    'assert_df_not_empty': assert_df_not_empty,
    'assert_minutes_played_gt_120': assert_minutes_played_gt_120,
    'assert_goals_in_range': assert_goals_in_range,
    'assert_assists_in_range': assert_assists_in_range,
    'assert_own_goals_in_range': assert_own_goals_in_range,
    'assert_yellow_cards_range': assert_yellow_cards_range,
    'assert_red_cards_range': assert_red_cards_range,
    'assert_unique_on_player_and_date': assert_unique_on_player_and_date,
    'assert_clubs_per_competition': assert_clubs_per_competition,
    'assert_games_per_season_per_club': assert_games_per_season_per_club,
    'assert_appearances_per_match': assert_appearances_per_match,
    'assert_appearances_per_club_per_game': assert_appearances_per_club_per_game,
    'assert_appearances_freshness_is_less_than_one_week': assert_appearances_freshness_is_less_than_one_week,
    'assert_goals_ne_own_goals': assert_goals_ne_own_goals,
    'assert_goals_ne_assists': assert_goals_ne_assists,
    'assert_yellow_cards_not_constant': assert_yellow_cards_not_constant,
    'assert_red_cards_not_constant': assert_red_cards_not_constant,
  }

  for validation in validations:
    try:
      validations_base[validation](df)
    except AssertionError as error:
      failed_validations+=1
      print(f"Validation {validation} did not pass: {error}")

  return failed_validations
