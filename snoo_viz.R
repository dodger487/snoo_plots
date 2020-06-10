library(tidyverse)
library(lubridate)

df <- read_csv("sample.csv", col_types = "Dcc")
df <- read_csv("rows.csv", col_types = "Dcc")
df <- read_csv("all_snoo_sessions.csv")


df <- df %>% mutate(start_time = as.POSIXct(start_time, format="%H:%M:%S", tz = "UTC"),
                    end_time = as.POSIXct(end_time, format="%H:%M:%S", tz = "UTC"))

df %>%
  mutate(
    st = hms(start_time),
    et = hms(end_time)
  ) %>%
ggplot(aes(x=start_date)) +
  geom_linerange(aes(ymin=st, ymax=et)) +
  scale_y_time()


df <- df %>% 
  mutate(
    id=row_number()
    # date = date(start_time)
    )
df %>% head
sessions <- df %>% 
  select(id, start_date, start_time, end_time) %>%
  gather(foo, relevant_time, start_time, end_time) %>%
  mutate(
    relevant_time = hms::as.hms(relevant_time),
    relevant_time = parse_date_time(relevant_time, "HMS")
  ) %>%
    # relevant_time = strptime(myDateTime, format="%d/%m/%Y %H:%M:%S"))) %>%
           # as.POSIXct(as.numeric(as.POSIXct(relevant_time)) %% 86400, origin = "2000-01-01")) %>%
  # mutate(relevant_time = as.POSIXct(relevant_time, format="%H:%M:%S", origin = "2020-01-01", tz = "UTC")) %>%
  arrange(id)
sessions %>% head  


################################################################################
##### Polar plot

# Read in data.
df <- read_csv("all_snoo_sessions.csv")


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


##### Plots!

# Cartesian axis plot faceted by awake v. asleep for debug purposes.
rows %>%
  ggplot(aes(xmin=start_time, xmax=end_time, 
             ymin=start_date, ymax=next_date,
             fill=session_type)) +
  geom_rect() +
  facet_wrap(~session_type)


# Cartesian axis plot for debug purposes.
rows %>%
  ggplot(aes(xmin=start_time, xmax=end_time, 
             ymin=start_date, ymax=next_date,
             fill=session_type)) +
  geom_rect()


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
  scale_fill_manual(values = c(color_awake, color_sleep)) +   # Custom colors
  theme_void() +                                              # Remove most axes.
  theme(legend.position = "none")                             # Remove legend.





ggplot(sessions, aes(x=relevant_time, y=start_date, group=id)) +
  geom_line()

63
89
123


248
205
160



sessions %>% 
  filter(date == "2019-11-30") %>%
  ggplot(aes(x=relevant_time, y=date, group=id)) +
  geom_line()

sessions %>%
  ggplot(aes(x=relevant_time, y=start_date, group=id)) +
  geom_line()

sessions %>%
  mutate(next_date = start_date)
  ggplot(aes(x=relevant_time, y=start_date, group=id)) +
  geom_rect(aes())

sessions %>%
  ggplot(aes(x=relevant_time, y=start_date, group=id)) +
  geom_line() +
  coord_polar(start=0) + 
  scale_x_datetime(date_breaks="1 hour", date_labels="%H:%M") +
  scale_y_date(expand=c(0, 28, 0, 0.0001)) +  # add margin on circle interior
  ylab("") +
  theme_void() 
ggsave("fig/radialplot.png")


df %>% head

df %>% mutate(start_time = hms(start_time))


df <- df %>% mutate(start_time = as.POSIXct(start_time, format="%H:%M:%S", tz = "UTC"),
                    end_time = as.POSIXct(end_time, format="%H:%M:%S", tz = "UTC"))

df %>% head

as.POSIXct(df$start_time, "%H:%M:%S", tz = "UTC")

df %>%
  ggplot(aes(x=start_date)) +
  geom_linerange(aes(ymin = start_time, ymax = end_time)) + 
  scale_y_datetime(date_breaks="1 hour", date_labels="%H:%M", expand = c(0,0)) +
  xlab("") +
  ggtitle("Baby Sleep Times") +
  theme_minimal() 
ggsave("fig/lineplot.png")


foo <- pd

df %>% head



df %>%
  ggplot(aes()) +
  geom_linerange(aes(x=start_date, ymin = start_time, ymax = end_time)) +
  coord_polar()
