# Chris Riederer
# 2020-06-05

"""Visualize Baby's sleep times by daytime or nighttime."""


import datetime

import numpy as np
from palettable.colorbrewer.qualitative import Paired_10
from palettable.lightbartlein.diverging import BlueGray_2
from palettable.cartocolors.qualitative import Vivid_2
import pandas as pd
from plotnine import *
from siuba import *


COLOR_VALUES = BlueGray_2

TIME_07_59_AM = datetime.time(hour= 7, minute=59, second=59)
TIME_07_59_PM = datetime.time(hour=19, minute=59, second=59)
TIME_11_59_PM = datetime.time(hour=23, minute=59, second=59)


# first, run 
# pip install snoo
# snoo sessions --start START_DATE --end END_DATE > all_snoo_sessions.csv
# df = pd.read_csv("all_snoo_sessions.csv")
df = pd.read_csv("all_snoo_sessions_2020-06-05.csv")


# Convert to pandas datetime.
df["start_datetime"] = pd.to_datetime(df["start_time"])
df["end_datetime"] = pd.to_datetime(df["end_time"])


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


# Simplify dataframe and split at midnight, 7am, and 7pm.
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
                                     "Night", 
                                     "Day"))


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
  + guides(fill=guide_legend(title=""))
  + theme(subplots_adjust={'right': 0.85})  # Give legend 10% so it fits
)
print(plot_rect)
ggsave(
  plot_rect, 
  "fig/rectplot_python_by_sleeptype.png",
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
  "fig/lineplot_python_sleepperday_by_sleeptype.png",
  width=6.96, height=5.51, units="in", dpi=300
)


# Get total time sleeping per day.
sleep_per_day = (sleep_per_day >>
  # Filter to when the data is accurate.
  filter(_.start_date >= datetime.date(year=2020, month=3, day=24),
         _.start_date <  datetime.date(year=2020, month=6, day= 5)) >>
  group_by(_.start_date) >>
  mutate(sleep_proportion = _.sleep_hours / _.sleep_hours.sum()) >>
  ungroup()
)


# Plot total time spent sleeping by night vs day.
plot_bar_day = (sleep_per_day >> 
  ggplot(aes(x="start_date", y="sleep_hours", fill="sleep_type"))
  + geom_col(position = position_stack(reverse = True))  # Put night on top of day
  + scale_x_date(name="", date_labels="%b %d") 
  + ylab("Hours of Sleep")
  + theme_bw()
  + scale_fill_manual(values=COLOR_VALUES.hex_colors)
  + theme(subplots_adjust={'right': 0.85})             # Give legend 10% so it fits
  + guides(fill=guide_legend(title=""), reverse=True)  # Reverse isn't implemented yet
  + scale_y_continuous(expand=(0, 0, 0, 0.0001))
)
print(plot_bar_day)
ggsave(
  plot_bar_day,
  "fig/barplot_python_by_sleeptype.png",
  width=6.96, height=5.51, units="in", dpi=300
)


# Plot proportion of time spent sleeping by night vs day.
plot_bar_pct = (sleep_per_day >> 
  ggplot(aes(x="start_date", y="sleep_proportion", fill="sleep_type"))
  + geom_col(position = position_stack(reverse = True))  # Put night on top of day
  + scale_x_date(name="", date_labels="%b %d") 
  + ylab("Percent of Total Sleep")
  + theme_bw()
  + scale_fill_manual(values=COLOR_VALUES.hex_colors)
  + theme(subplots_adjust={'right': 0.85})             # Give legend 10% so it fits
  + guides(fill=guide_legend(title=""), reverse=True)  # Reverse isn't implemented yet
  + scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l],  # % labels
                       expand=(0, 0, 0, 0.0001))       # No white margins on graphs
)
print(plot_bar_pct)
ggsave(
  plot_bar_pct,
  "fig/barplot_python_pct_sleeptype.png",
  width=6.96, height=5.51, units="in", dpi=300
)