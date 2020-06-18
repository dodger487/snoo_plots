# Chris Riederer
# 2020-05-28
# Make radial plot of baby's sleep times.

# To get data, make sure pip is installed. Then:
# pip install snoo
# snoo sessions --start START_DATE --end END_DATE > sleep_data.csv


################################################################################
##### Read and manipulate data.

# Read in data.
df <- read_csv("sleep_data.csv")


# Add rows for when baby is awake, the inverse of when baby is asleep.
df <- df %>%
  select(-duration, -asleep, -soothing) %>%
  mutate(session_type = "asleep") 
inverse_df <- df %>%
  arrange(start_time) %>%
  mutate(
    start_time_new = end_time,
    end_time_new = lead(start_time),
    session_type = "awake",
    start_time = start_time_new,
    end_time = end_time_new
  ) %>%
  select(-start_time_new, -end_time_new) %>%
  filter(!is.na(start_time) & !is.na(end_time))

# Combine the "awake" and "asleep" rows.
df <- rbind(df, inverse_df) %>% arrange(start_time)


# Break up sessions that cross the midnight boundary into two sessions,
# one pre-midnight and one-after midnight, so that all sessions only take place
# in one day.
df_no_cross <- df %>% 
  filter(date(start_time) == date(end_time)) %>%
  mutate(
    start_date = date(start_time), 
    next_date = start_date + days(1),
    start_time = hms::as_hms(start_time),
    end_time = hms::as_hms(end_time))

df_cross <- df %>% filter(date(start_time) != date(end_time))
df_cross_1 <- df_cross %>% 
  mutate(
    start_date = date(start_time), 
    next_date = start_date + days(1),
    start_time = hms::as_hms(start_time),
    end_time = hms::as_hms("23:59:59")
  )
df_cross_2 <- df_cross %>% 
  mutate(
    start_date = date(end_time), 
    next_date = start_date + days(1),
    start_time = hms::as_hms("00:00:00"),
    end_time = hms::as_hms(end_time)
  )

# Combine dataframes.
rows <- rbind(
  df_no_cross,
  df_cross_1,
  df_cross_2
)


################################################################################
##### Plots!

# Cartesian axis plot faceted by awake v. asleep for debug purposes.
rows %>%
  ggplot(aes(xmin=start_time, xmax=end_time, 
             ymin=start_date, ymax=next_date,
             fill=session_type)) +
  geom_rect() +
  facet_wrap(~session_type)
ggsave("fig/test_facet.png")


# Cartesian axis plot for debug purposes.
rows %>%
  ggplot(aes(xmin=start_time, xmax=end_time, 
             ymin=start_date, ymax=next_date,
             fill=session_type)) +
  geom_rect()
ggsave("fig/test_rect.png")

# Prelim plot 1: Recreate the Python plot
p <- (rows %>%
    filter(session_type == "asleep") %>%
    ggplot(aes(x=start_date), data=.)
  + geom_linerange(aes(ymin = start_time, ymax = end_time))
  + scale_x_date(name="", date_labels="%b", expand=c(0, 0)) 
  + scale_y_time(labels = function(x) format(as.POSIXct(x), format = '%H:%M'),
                 expand=c(0, 0, 0, 0.0001))
  + ggtitle("Baby Sleep Times")
  + theme_minimal() 
)
p
ggsave("fig/lineplot_r.png")

# Prelim plot 2: Same as above, just add "coord_polar"
(rows %>%
    filter(session_type == "asleep") %>%
    ggplot(aes(x=start_date), data=.)
  + geom_linerange(aes(ymin = start_time, ymax = end_time))
  + scale_x_date(name="", date_labels="%b", expand=c(0, 0)) 
  + scale_y_time(labels = function(x) format(as.POSIXct(x), format = '%H:%M'),
                 expand=c(0, 0, 0, 0.0001))
  + ggtitle("Baby Sleep Times")
  + theme_minimal() 
  + coord_polar(start = 0)
)
ggsave("fig/polar_wrong.png")
# Could also just run...
p + coord_polar(start=0)

# Prelim plot 3: Rotated version of Python plot, using geom_rect, not geom_linerange
p2 <- (rows %>%
    filter(session_type == "asleep") %>%
    ggplot(aes())
    + geom_rect(aes(xmin = start_time, xmax = end_time,
                    ymin = start_date, ymax = next_date,))
    + scale_y_date(name="", date_labels="%b", expand=c(0, 0)) 
    + scale_x_time(expand=c(0, 0, 0, 0.0001))
    + ggtitle("Baby Sleep Times")
    + theme_minimal() 
)
p2
ggsave("fig/rectplot_rotate_r.png")


# Prelim plot 4: Same as above, just add coord_polar
(rows %>%
    filter(session_type == "asleep") %>%
    ggplot(aes())
  + geom_rect(aes(xmin = start_time, xmax = end_time,
                  ymin = start_date, ymax = next_date,))
  + scale_y_date(name="", date_labels="%b", expand=c(0, 0)) 
  + scale_x_time(expand=c(0, 0, 0, 0.0001))
  + ggtitle("Baby Sleep Times")
  + theme_minimal() 
  + coord_polar()
)
ggsave("fig/rectplot_polar_r.png")

# Alternatively, just change the theta mapping from the unrotated line plot:
p + coord_polar(theta = "y", start=0)


# Create custom colors, pulled from original plot via OSX's Digital Color Meter.
color_awake <- rgb(248/256, 205/256, 160/256)
color_sleep <- rgb(63/256, 89/256, 123/256)


# Create radial plot
rows %>% 
  filter(start_date <= "2020-05-20") %>%
  ggplot(aes(xmin = start_time, xmax = end_time, 
             ymin = start_date, ymax = next_date,
             fill = session_type)) +
  geom_rect(color=NA) +                                       # Make sure no edge colors on rectangle.
  coord_polar(start = 0) +                                    # Apply polar coordinates.
  scale_y_date(expand = c(0, 28, 0, 0.0001)) +                # Add margin on circle interior.
  scale_fill_manual(values = c(color_sleep, color_awake)) +   # Custom colors
  theme_void() +                                              # Remove most axes.
  theme(legend.position = "none")                             # Remove legend.
ggsave("fig/polar_rectplot_colorful.svg")


# Create radial plot using geom_lineplot instead of geom_rect
(rows %>%
  filter(start_date <= "2020-05-20") %>%
  ggplot(aes(x=start_date), data=.)
+ geom_linerange(aes(ymin = start_time, ymax = end_time, color = session_type))
+ scale_x_date(name="", date_labels="%b", expand=c(0, 28))    # Add margin on circle interior.
+ scale_y_time(expand=c(0, 0, 0, 0.0001))                     # Remove margin.
+ scale_color_manual(values = c(color_sleep, color_awake))    # Custom colors
+ theme_void()                                                # Remove most axes.
+ coord_polar(theta = "y")                                    # Apply polar coordinates.
+ theme(legend.position = "none",                             # Remove legend.
        plot.margin = margin(-2, -2, -2, -2, "cm"))
)
ggsave("fig/polar_lineplot_colorful.svg", height=5, width=5, units="in")
ggsave("fig/polar_lineplot_colorful.png", height=5, width=5, units="in")
