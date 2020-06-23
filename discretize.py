# Chris Riederer
# 2020-06-20

# Discretize a timeseries using Pandas


import datetime as dt

import numpy as np
from palettable.lightbartlein.diverging import BlueGray_2
import pandas as pd
from plotnine import *
from scipy.spatial import distance


# Constants
COLOR_VALUES = BlueGray_2

ONE_SECOND = dt.timedelta(seconds = 1)
FIFTEEN_MINUTES = dt.timedelta(minutes = 15)
ONE_DAY = dt.timedelta(days = 1)


# Read in data
df = pd.read_csv("sleep_data.csv")


# Break out dates and times.
df["start_datetime"] = pd.to_datetime(df["start_time"])
df["end_datetime"] = pd.to_datetime(df["end_time"])
df["start_time"] = df["start_datetime"].dt.time
df["end_time"] = df["end_datetime"].dt.time
df["start_date"] = df["start_datetime"].dt.date


## Part 1: Combine start and end times into one series.
start_times = df[["start_datetime"]].copy()
start_times.columns = ["timestamp"]  # Rename column.
start_times["is_asleep"] = 1

end_times = df[["end_datetime"]].copy()
end_times.columns = ["timestamp"]  # Rename column.
end_times["is_asleep"] = 0

all_times = pd.concat([start_times, end_times]).sort_values("timestamp")

# Handle an annoying issue where duplicate timestamps breaks resampling later.
all_times["timestamp"] = np.where(all_times.timestamp == all_times.timestamp.shift(-1),
                                  all_times.timestamp + ONE_SECOND,
                                  all_times.timestamp)

all_times = all_times.set_index("timestamp")


## Part 2: Discretize from any time period to evenly distributed periods.
# Discretize Method 1: Quick (and slow?) and dirty
disc_1 = all_times.resample("1S").ffill().resample("15min").max()


# Discretize Method 2: Combine max to get the right value, last + ffill to get fills
r = all_times.resample("15min")
r_last = r.last().fillna(method = "ffill")
r_max = r.max()
r_max[~r_max.isna().values] = 1  # If it contains a value, set it to 1, else leave null

disc_2 = r_max.combine_first(r_last).astype(int)


# Prove that they're the same!
assert disc_1.equals(disc_2)


# Can use the following functions with %timeit fo ra speed test
def method_1():
  return all_times.resample("1S").ffill().resample("15min").max()

def method_2():
  r = all_times.resample("15min")
  r_max = r.max()
  r_max[~r_max.isna().values] = 1  # If it contains a value, set it to 1, else leave null
  r_last = r.last().fillna(method = "ffill")

  return r_max.combine_first(r_last).astype(int)


## Part 3: Transform from one discretized time series into one vector per day.
# Filter to full days
disc_1 = disc_1[(disc_1.index >= pd.to_datetime("2019-11-22"))
                & (disc_1.index < pd.to_datetime("2020-06-05"))]


num_periods = int(ONE_DAY / FIFTEEN_MINUTES)


# Featurize Method 1: Simply use a reshape
ftrs_1 = disc_1.values.reshape(len(disc_1) // num_periods, num_periods)


# Featurize Method 2: Use a pivot table
ftrs_2 = disc_1.reset_index()
ftrs_2["date"] = ftrs_2.timestamp.dt.date
ftrs_2["time"] = ftrs_2.timestamp.dt.time
ftrs_2 = ftrs_2.pivot(index="date", columns="time", values="is_asleep")


# Prove that they're the same!
assert (ftrs_1 == ftrs_2).all(axis=None)


## Part 4: Compute cosine similarity between vectors
# Compute it. Cos Similarity = 1 - Cos Distance
similarity = [1 - distance.cosine(i, j) for i, j 
              in zip(ftrs_2.iloc[0:-1].values, ftrs_2.iloc[1:].values)]


# Make a DataFrame for easy plotting
plot_df = pd.DataFrame({
  "date": ftrs_2.index[1:],  # Remove the first row, since we don't have a similarity for it.
  "similarity": similarity,
})


# Plot it!
plot = (ggplot(aes(x = "date", y = "similarity", group = 1), data=plot_df) 
  + geom_line(color = COLOR_VALUES.hex_colors[1])
  + scale_x_date(name="", date_labels="%b", expand=(0, 0)) 
  + ylab("Similarity to Previous Day")
  + geom_smooth(color = COLOR_VALUES.hex_colors[0])
  + theme_bw()
  + ggtitle("Baby Sleep Regularity")
  )
print(plot)
ggsave(
  plot,
  "fig/lineplot_time_cossimilarity.png",
  width=6.96, height=5.51, units="in", dpi=300
)