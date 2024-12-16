require(tidyverse)
require(lubridate)
require(sf)
require(terra)
require(raster)
require(censusapi)
require(tigris)

mutate_cond <- function (.data, condition, ..., envir = parent.frame()) {
  condition <- eval(substitute(condition), .data, envir)
  .data[condition, ] <- .data[condition, ] %>% mutate(...)
  .data
}

files_to_load <- list.files("data", full.names = TRUE)

combined <- read_csv(files_to_load[1])

for (i in 2:length(files_to_load)){
  
    newfile <- suppressMessages(read_csv(files_to_load[i]))
    
    print(i)
    print(files_to_load[i])
    print(nrow(newfile))
    
    if (nrow(newfile) > 0){
      
      combined <- combined %>%
        full_join(newfile)
    }

}

dat2 <- combined %>%
  filter(temp_C > 6) %>%
  filter(!is.na(lat)) %>%
  filter(!is.na(long)) %>%
  filter(CO2_ppm > 10) 

dat2 <- dat2 %>%
  filter(!str_detect(datetime, "0/0/0")) %>%
  mutate(datetime = mdy_hms(datetime)) %>%
  mutate(location = st_as_sf(., coords = c("long", "lat"), crs = 4326))

View(dat2)

plot(dat2$particles05um ~ dat2$particles03um, xlab = "PM03 (ppm)", 
     ylab = "PM05 (ppm)", main = "PM03 vs. PM05", xlim = c(0, 4200),
     las = 1, ylim = c(0, 1350), col.main = "red")

list.files(recursive = TRUE)

bc2122 <- rast("Data/nyc_pm_bc/aa14_bc300m/hdr.adf")
pm2122 <- rast("Data/nyc_pm_bc/aa14_pm300m/hdr.adf")

plot(pm2122)
newcrs <- "+proj=longlat +datum=WGS84"
bc2122.wgs <- project(bc2122, newcrs)
pm2122.wgs <- project(pm2122, newcrs)

small.extent <- raster::extent(-74.1, -73.8, 40.6, 40.9)

pm2122.wgs.crop <- crop(pm2122.wgs, small.extent)
bc2122.wgs.crop <- crop(bc2122.wgs, small.extent)

dat <- read_csv("Data/extracted_census_data.csv") %>%
  filter(projectname == "socioeconomic")

pts <- vect(cbind(dat$longitude, dat$latitude), atts=dat[, c(1, 3:15, 18)])

par(mfrow = c(1))
plot(bc2122.wgs.crop)
plot(pm2122.wgs.crop)
points(pts, col = "yellow")

apis <- listCensusApis()

# Define the variables for income and poverty
variables <- c("B19013_001E",  # Median household income
               "B17021_001E",  # Total population in poverty
               "B01003_001E")  # Total population

state_fips <- "36"  # New York state
county_fips <- c("005", "047", "061", "081", "085")  # Bronx, Brooklyn, Manhattan, Queens, Staten Island

# Make the API call for ACS 5-year data (2021)
census_data <- getCensus(
  name = "acs/acs5",  # Dataset name
  vintage = 2021,  # Year of data
  vars = variables,  # Variables to fetch
  region = "tract:*",  # All census tracts
  regionin = paste0("state:", state_fips, " + county:", paste(county_fips, collapse = ",")),
  key = "dde93d3f5e7d70a2168ea41267c42f1a020d4b96"
)
census_data <- census_data %>%
  mutate(GEOID = paste0(state, county, tract))  # Create GEOID in the tabular data

# View the resulting data
head(census_data)

# Step 2: Download Spatial Data for Census Tracts
nyc_tracts <- tigris::tracts(state = state_fips, cb = FALSE, year = 2021)

nyc_tracts <- nyc_tracts %>% 
  filter(COUNTYFP %in% county_fips)

# Step 3: Join Tabular Data with Spatial Data
# Ensure `GEOID` is the common identifier
nyc_data <- nyc_tracts %>%
  left_join(census_data, by = "GEOID")  # Join the data

## make sure the census data are in the same crs as the other data
nyc_data.wgs <- st_transform(nyc_data, crs = newcrs)

## convert points to sf object
points_sf <- st_as_sf(dat2, coords = c("long", "lat"), crs = newcrs) # Assuming WGS84

## spatial join
joined_census_data <- st_join(points_sf, nyc_data.wgs) %>% 
  mutate(latitude = st_coordinates(.)[, 2],  # Y-coordinate
         longitude = st_coordinates(.)[, 1])  # X-coordinate

## select only specific variables to output
extracted_census_data <- joined_census_data %>% 
  st_drop_geometry() %>% 
  dplyr::select(1:12, median_household_income = B19013_001E, ppn_poverty = B17021_001E, ppn_total = B01003_001E, latitude, longitude) %>% 
  mutate_cond(median_household_income < 0,  median_household_income = NA) %>% 
  mutate_cond(ppn_poverty < 0,  ppn_poverty = NA) %>% 
  mutate_cond(ppn_total < 0,  ppn_total = NA) %>% 
  mutate(poverty_rate = ppn_poverty/ppn_total)

write_csv(extracted_census_data, "Data/extracted_census_data.csv")

plot(dat2$particles03um ~ extracted_census_data$median_household_income, xlab = "Median Household Income", 
     ylab = "PM03 Concentration (ppm)", main = "PM05 Concentration vs. Household Income",
     las = 1, ylim = c(0, 4250), col.main = "red")

# NEED TO DETERMINE HOW MUCH DATA WE HAVE FOR EACH CENSUS AREA INCOME 