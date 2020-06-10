# Chris Riederer
# 2020-06-05

"""Visualize Baby's snoo data."""


import datetime

import numpy as np
from palettable.colorbrewer.qualitative import Paired_10
from palettable.lightbartlein.diverging import BlueGray_2
from palettable.cartocolors.qualitative import Vivid_2
import pandas as pd
from plotnine import *
from siuba import *


COLOR_VALUES = Vivid_2
# COLOR_VALUES = BlueGray_2

TIME_07_59_AM = datetime.time(hour= 7, minute=59, second=59)
TIME_07_59_PM = datetime.time(hour=19, minute=59, second=59)
TIME_11_59_PM = datetime.time(hour=23, minute=59, second=59)


def split_times(df, time_to_split):
  df = df >> mutate(start_date = _.start_datetime.dt.date, 
                    split_time = time_to_split)
  df["split_time"] = df.apply(lambda X: datetime.datetime.combine(X.start_date, X.split_time), axis=1)

  df_no_cross = (df >> 
    filter(~((_.start_datetime < _.split_time)
             & (_.end_datetime > _.split_time))))
  df_cross = (df >> 
    filter(_.start_datetime < _.split_time,
           _.end_datetime > _.split_time))

  df_cross_1 = df_cross.copy() >> mutate(end_datetime = _.split_time)
  df_cross_2 = (df_cross.copy() 
    >> mutate(start_datetime = _.split_time + datetime.timedelta(seconds=1)))

  df = pd.concat([df_no_cross, df_cross_1, df_cross_2])
  df = select(df, _.start_datetime, _.end_datetime)
  return df


# first, run 
# pip install snoo
# snoo sessions --start START_DATE --end END_DATE > all_snoo_sessions.csv
df = pd.read_csv("all_snoo_sessions_2020-06-05.csv")
# df = pd.read_csv("all_snoo_sessions.csv")


# Break out dates and times.
df["start_datetime"] = pd.to_datetime(df["start_time"])
df["end_datetime"] = pd.to_datetime(df["end_time"])

df = select(df, _.start_datetime, _.end_datetime)
df = split_times(df, TIME_11_59_PM)  # Split timestamps that cross days.
df = split_times(df, TIME_07_59_AM)  # 12am - 7am is night.
df = split_times(df, TIME_07_59_PM)  # 7pm - 12am is night.


# Make columns for date and time of day
df["start_time"] = df["start_datetime"].dt.time
df["end_time"] = df["end_datetime"].dt.time
df["start_date"] = df["start_datetime"].dt.date
df["end_date"] = df.start_datetime.dt.date + datetime.timedelta(days=1)


# Add a "night" or "day" column based on time of day.
df = mutate(df, sleep_type = if_else(((_.start_time > TIME_07_59_PM)
                                      | (_.start_time <= TIME_07_59_AM)), 
                                     "night", 
                                     "day"))


# Convert start_time from datetime.time to datetime64 for plotting.
df["start_time"] = pd.to_datetime(df["start_datetime"].dt.time, format='%H:%M:%S')
df["end_time"] = pd.to_datetime(df["end_datetime"].dt.time, format='%H:%M:%S')


# Plot sleep times by day, colored by time of day.
plot_rect = (
  ggplot(aes(), data=df)
  + geom_rect(aes(xmin = "start_date", xmax = "end_date",
                  ymin = "start_time", ymax = "end_time",
                  fill = "sleep_type"))
  + scale_x_date(name="", date_labels="%b") 
  + scale_y_datetime(
        date_labels="%H:%M",
        expand=(0, 0, 0, 0.0001))
  + ggtitle("Baby Sleep Times")
  + theme_bw() 
  + scale_fill_manual(values=COLOR_VALUES.hex_colors)
  + guides(color=guide_legend(title=""))
  + theme(subplots_adjust={'right': 0.85})  # Give legend 10% so it fits
)
print(plot_rect)
ggsave(
  plot_rect, 
  "fig/lineplot_python_by_sleeptype.png",
  width=6.96, height=5.51, units="in", dpi=300
)


# Aggregate days into daytime and nighttime sleep.
sleep_per_day = (df 
  >> mutate(session_length = _.end_datetime - _.start_datetime)
  >> group_by(_.start_date, _.sleep_type) 
  >> summarize(sleep_time = _.session_length.sum())
  >> mutate(sleep_hours = _.sleep_time /  np.timedelta64(1, 'h'))  # convert to hours
)


# Plot amount of sleep per day, by daytime or nighttime.
plot_spd = (sleep_per_day >>
  ggplot(aes(x = "start_date", y = "sleep_hours", 
             color="sleep_type", group = "sleep_type")) 
  + geom_line() 
  + scale_x_date(name="", date_labels="%b") 
  + ylab("Hours of Sleep")
  + geom_smooth(span=0.3)
  + theme_bw()
  + scale_color_manual(values=COLOR_VALUES.hex_colors)
  + theme(subplots_adjust={'right': 0.85})  # Give legend 10% so it fits
  + guides(color=guide_legend(title=""))
)
print(plot_spd)
ggsave(
  plot_spd, 
  "fig/rectplot_python_by_sleeptype.png",
  width=6.96, height=5.51, units="in", dpi=300
)








(agg_rows 
  >> ggplot(aes(x = "start_date", y = "total_sleep", group=1)) 
  + theme_bw()
  + geom_line() 
  + scale_x_datetime() 
  + ylab("")
  + theme(axis_text_x=element_text(angle = 45)) 
  + geom_smooth(color="blue", span=0.3)
  + ggtitle("Hours of Sleep by Day")
)










# Deal with sessions that cross day boundaries.
df_no_cross = df[df["start_datetime"].dt.day == df["end_datetime"].dt.day].copy()
df_cross = df[df["start_datetime"].dt.day != df["end_datetime"].dt.day]
df_cross_1 = df_cross.copy()
df_cross_2 = df_cross.copy()
df_cross_1["end_time"] = datetime.time(hour=23, minute=59, second=59)
df_cross_2["start_date"] = df_cross_2["start_date"] + datetime.timedelta(days=1)
df_cross_2["start_time"] = datetime.time(hour=0, minute=0, second=0)


# Combine dataframes
rows_no_cross = df_no_cross[["start_date", "start_time", "end_time"]]
rows_cross_1 = df_cross_1[["start_date", "start_time", "end_time"]]
rows_cross_2 = df_cross_2[["start_date", "start_time", "end_time"]]
rows = pd.concat([rows_no_cross, rows_cross_1, rows_cross_2])


# Convert to Pandas Datetime to make plotting easier.
# rows["start_time"] = pd.to_datetime(rows["start_time"], format='%H:%M:%S')
# rows["end_time"] = pd.to_datetime(rows["end_time"], format='%H:%M:%S')


def split_times(df, split_time):
  """Given a dataframe containing rows with start and end times, split 
  sessions into two separate sessions at a certain time."""

  def earlier_time(split_time):
    return (datetime.datetime.combine(datetime.date(1,1,1), split_time)
            - datetime.timedelta(seconds=1)).time()

  df_no_cross = (df >> 
    filter(~((_.start_time < split_time)
             & (_.end_time > split_time))))
  df_cross = (df >> 
    filter(_.start_time < split_time,
           _.end_time > split_time))

  df_cross_1 = df_cross.copy()
  df_cross_2 = df_cross.copy()
  df_cross_1["end_time"] = earlier_time(split_time)
  df_cross_2["start_time"] = split_time

  return pd.concat([df_no_cross, df_cross_1, df_cross_2])


def split_times2(df, split_time):
  """Given a dataframe containing rows with start and end times, split 
  sessions into two separate sessions at a certain time."""

  def earlier_time(split_time):
    return (datetime.datetime.combine(datetime.date(1950,1,1), split_time)
            - datetime.timedelta(seconds=1)).time()

  df_no_cross = (df >> 
    filter(~((_.start_datetime.dt.time < split_time)
             & (_.end_datetime.dt.time > split_time))))
  df_cross = (df >> 
    filter(_.start_datetime.dt.time < split_time,
           _.end_datetime.dt.time > split_time))

  df_cross_1 = df_cross.copy()
  df_cross_2 = df_cross.copy()
  df_cross_1["end_datetime"] = earlier_time(split_time)
  df_cross_2["start_datetime"] = split_time

  return pd.concat([df_no_cross, df_cross_1, df_cross_2])


def earlier_time(split_time):
  return (datetime.datetime.combine(datetime.date(1950,1,1), split_time)
          - datetime.timedelta(seconds=1)).time()


def split_times3(df, time_to_split):
  df = df >> mutate(start_date = _.start_datetime.dt.date, 
                    split_time = time_to_split)
  df["split_time"] = df.apply(lambda X: datetime.datetime.combine(X.start_date, X.split_time), axis=1)


  df_no_cross = (df >> 
    filter(~((_.start_datetime < _.split_time)
             & (_.end_datetime > _.split_time))))
  df_cross = (df >> 
    filter(_.start_datetime < _.split_time,
           _.end_datetime > _.split_time))

  df_cross_1 = df_cross.copy()
  df_cross_2 = df_cross.copy()
  df_cross_1["end_datetime"] = df["split_time"]
  df_cross_2["start_datetime"] = df["split_time"] + datetime.timedelta(seconds=1)

  df = pd.concat([df_no_cross, df_cross_1, df_cross_2])
  df = select(df, _.start_datetime, _.end_datetime)
  return df.reset_index(drop=True)


df = df >> select()

def plot_it(df):
  df = df.copy()
  df["start_date"] = df.start_datetime.dt.date
  df["start_time"] = pd.to_datetime(df["start_datetime"].dt.time, format='%H:%M:%S')
  df["end_time"] = pd.to_datetime(df["end_datetime"].dt.time, format='%H:%M:%S')
  return (ggplot(aes(x="start_date",), data=df)
    + geom_linerange(aes(ymin = "start_time", ymax = "end_time"))
    + scale_x_date(name="", date_labels="%b", expand=(0, 0)) 
    + scale_y_datetime(date_labels="%H:%M",
                       expand=(0, 0, 0, 0.0001))
    + ggtitle("Baby Sleep Times")
    + theme_minimal() 
    + theme(plot_background=element_rect(color="white"))
  )


def plot_it2(df):
  df = df.copy()
  df["start_date"] = df.start_datetime.dt.date
  df["start_time"] = pd.to_datetime(df["start_datetime"].dt.time, format='%H:%M:%S')
  df["end_time"] = pd.to_datetime(df["end_datetime"].dt.time, format='%H:%M:%S')
  return (ggplot(aes(x="start_date",), data=df)
    + geom_linerange(aes(ymin = "start_time", ymax = "end_time", color="sleep_type"))
    + scale_x_date(name="", date_labels="%b", expand=(0, 0)) 
    + scale_y_datetime(date_labels="%H:%M",
                       expand=(0, 0, 0, 0.0001))
    + ggtitle("Baby Sleep Times")
    + theme_minimal() 
    + theme(plot_background=element_rect(color="white"))
  )


def plot_rect(df):
  df = df.copy()
  df["start_date"] = df.start_datetime.dt.date
  df["end_date"] = df.start_datetime.dt.date + datetime.timedelta(days=1)
  df["start_time"] = pd.to_datetime(df["start_datetime"].dt.time, format='%H:%M:%S')
  df["end_time"] = pd.to_datetime(df["end_datetime"].dt.time, format='%H:%M:%S')
  return (ggplot(aes(), data=df)
    + geom_rect(aes(xmin = "start_date", xmax = "end_date",
                    ymin = "start_time", ymax = "end_time",
                    fill = "sleep_type"))
    + scale_x_date(name="", date_labels="%b") 
    + ggtitle("Baby Sleep Times")
    + theme_minimal() 
    + theme(plot_background=element_rect(color="white"))
    + scale_y_datetime(
          date_labels="%H:%M",
          expand=(0, 0, 0, 0.0001))
  )

  return (ggplot(aes(x="start_date",), data=df)
    + geom_linerange(aes(ymin = "start_time", ymax = "end_time", color="sleep_type"))
    + scale_x_date(name="", date_labels="%b", expand=(0, 0)) 
    + scale_y_datetime(date_labels="%H:%M",
                       expand=(0, 0, 0, 0.0001))
    + ggtitle("Baby Sleep Times")
    + theme_minimal() 
    + theme(plot_background=element_rect(color="white"))
  )

  return (df >>
    mutate(
      start_date = _.start_datetime.dt.date,
      start_time = pd.to_datetime(rows["start_time"], format='%H:%M:%S')
      end_time = pd.to_datetime(rows["end_time"], format='%H:%M:%S')     )
    ggplot(aes())

ggplot(aes(x=""))

rows = split_times(rows, TIME_8_PM)
rows = (rows 
  >> mutate(sleep_time = if_else(_.start_time < TIME_8_PM, "day", "night")))
rows = (rows >>
  mutate(end_date = _.start_date + datetime.timedelta(days=1)))

# Convert to Pandas Datetime to make plotting easier.
rows["start_time"] = pd.to_datetime(rows["start_time"], format='%H:%M:%S')
rows["end_time"] = pd.to_datetime(rows["end_time"], format='%H:%M:%S')


foo["start_time"] = pd.to_datetime(foo["start_time"], format='%H:%M:%S')
foo["end_time"] = pd.to_datetime(foo["end_time"], format='%H:%M:%S')

plot = (ggplot(aes(x="start_date",), data=foo)
  + geom_linerange(aes(ymin = "start_time", ymax = "end_time"))
  + scale_x_date(name="", date_labels="%b", expand=(0, 0)) 
  + scale_y_datetime(date_labels="%H:%M",
                     expand=(0, 0, 0, 0.0001))
  + ggtitle("Baby Sleep Times")
  + theme_minimal() 
  + theme(plot_background=element_rect(color="white"))
)

(ggplot(aes(), data=rows)
  + geom_rect(aes(xmin = "start_date", xmax = "end_date",
                  ymin = "start_time", ymax = "end_time"))
  + scale_x_date(name="", date_labels="%b") 
  + ggtitle("Baby Sleep Times")
  + theme_minimal() 
  + theme(plot_background=element_rect(color="white"))
  + scale_y_datetime(
        date_labels="%H:%M", 
        limits=(pd.to_datetime("00:00:00", format='%H:%M:%S'),
                pd.to_datetime("22:59:59", format='%H:%M:%S')))
  # + ylim((pd.to_datetime("00:00:00", format='%H:%M:%S'),
  #               pd.to_datetime("22:59:59", format='%H:%M:%S')))
)

# Things to plot:
# - Sleep per day, with smoothing
# - Nighttime sleep
# - Number of naps...?


agg_rows = (rows 
  >> mutate(sleep_time = _.end_time - _.start_time)
  >> group_by(_.start_date) 
  >> summarize(
    total_sleep = _.sleep_time.sum(), 
    long_naps = (_.sleep_time > datetime.timedelta(minutes=15)).sum()),
)


# Plot amount of sleep per day
(agg_rows 
  >> ggplot(aes(x = "start_date", y = "total_sleep", group=1)) 
  + theme_bw()
  + geom_line() 
  + scale_x_datetime() 
  + ylab("")
  + theme(axis_text_x=element_text(angle = 45)) 
  + geom_smooth(color="blue", span=0.3)
  + ggtitle("Hours of Sleep by Day")
)


