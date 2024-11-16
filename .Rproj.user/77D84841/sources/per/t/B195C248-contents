require(tidyverse)
require(lubridate)
require(sf)

tempdata<-read_csv("data/10 28.csv")

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