# Chris Riederer
# 2020-05-24

"""Visualize Baby's snoo data."""


import datetime

import pandas as pd
from plotnine import *


# first, run 
# pip install snoo
# snoo sessions --start START_DATE --end END_DATE > sleep_data.csv
df = pd.read_csv("sleep_data.csv")

# Break out dates and times.
df["start_datetime"] = pd.to_datetime(df["start_time"])
df["end_datetime"] = pd.to_datetime(df["end_time"])
df["start_time"] = df["start_datetime"].dt.time
df["end_time"] = df["end_datetime"].dt.time
df["start_date"] = df["start_datetime"].dt.date


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
rows["start_time"] = pd.to_datetime(rows["start_time"], format='%H:%M:%S')
rows["end_time"] = pd.to_datetime(rows["end_time"], format='%H:%M:%S')


# Make the plot.
plot = (ggplot(aes(x="start_date",), data=rows)
  + geom_linerange(aes(ymin = "start_time", ymax = "end_time"))
  + scale_x_date(name="", date_labels="%b", expand=(0, 0)) 
  + scale_y_datetime(date_labels="%H:%M",
                     expand=(0, 0, 0, 0.0001))
  + ggtitle("Baby Sleep Times")
  + theme_minimal() 
  + theme(plot_background=element_rect(color="white"))
)

# Save it!
ggsave(plot, "fig/lineplot_python.png", width=6.96, height=5.51, units="in", dpi=300)
