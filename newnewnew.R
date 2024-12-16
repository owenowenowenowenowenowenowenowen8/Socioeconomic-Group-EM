require(tidyverse)
require(terra)
require(sf)
require(censusapi)
require(tigris)
require(lubridate)

dat <- read_csv("Data/alldata(1).csv")

DataFile <- read_csv("Data/alldata(2).csv")

DataFile.proj <- DataFile %>%
  filter(projectname == "socioeconomic") %>%
  filter(!is.na(median_household_income))

DataFile.proj <- vect(cbind(DataFile.proj$longitude, DataFile.proj$latitude)
  , atts = DataFile.proj[, 1:23]
  , crs = newcrs)

newcrs <- "+proj=longlat +datum=WGS84"
small.extent <- raster::extent(-74.1, 73.8)

plot(DataFile.proj$particles03um ~ DataFile.proj$CO2_ppm)