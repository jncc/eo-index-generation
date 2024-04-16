#####Process Living England chunks as shapefiles #####

suppressPackageStartupMessages(
  suppressWarnings({
    require(magrittr)
    require(raster)
    require(rgdal)
    require(sf)
    require(dplyr)
    require(stringr)
  })
)

zone1<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ01.shp")
zone2<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ02.shp")
zone3<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ03.shp")
zone4<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ04.shp")
zone5<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ05.shp")
zone6<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ06.shp")
zone7<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ07.shp")
zone8<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ08.shp")
zone9<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ09.shp")
zone10<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ10.shp")
zone11<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ11.shp")
zone12<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ12.shp")
zone1314<-st_read("./PhaseIV_Final_byBGZ/LivingEngland_HabitatProbability_Phase4_BGZ1314.shp")

###Check all polygon ids are unique and equal the number in all England file 
zone1_ids<-unique(zone1$ID)
zone2_ids<-unique(zone2$ID)
zone3_ids<-unique(zone3$ID)
zone4_ids<-unique(zone4$ID)
zone5_ids<-unique(zone5$ID)
zone6_ids<-unique(zone6$ID)
zone7_ids<-unique(zone7$ID)
zone8_ids<-unique(zone8$ID)
zone9_ids<-unique(zone9$ID)
zone10_ids<-unique(zone10$ID)
zone11_ids<-unique(zone11$ID)
zone12_ids<-unique(zone12$ID)
zone1314_ids<-unique(zone1314$ID)

all_ids<-c(zone1_ids, zone2_ids, zone3_ids, zone4_ids, zone5_ids, zone6_ids, zone7_ids, zone8_ids, zone9_ids, zone10_ids, zone11_ids, zone12_ids,zone1314_ids)

length(unique(all_ids))
anyDuplicated(all_ids)

#Assign variables
idfield<-"ID"
habfield<-"A_pred"
habremove<-"Unclassified"
outpath<-"./BGZ_processed/"

process_sf<-function(sf){
  
  #Read in spatial framework and assign field names to variables
  polygons <- sf::st_read(sf, quiet = T, stringsAsFactors = F) %>%
    dplyr::mutate(area_m = st_area(geometry))%>%
    units::drop_units()%>%
    dplyr::select(idfield, habfield, area_m) %>%
    dplyr::rename(POLYID = 1, HABITAT = 2, AREA = 3)%>%
    dplyr::mutate(POLYID = as.character(POLYID), HABITAT = as.character(HABITAT), AREA = as.numeric(AREA))
  
  #Remove irrelevant habitats and minor polygons
  if (is.null(habremove)){
    poly_clean<-polygons%>%
      dplyr::filter(AREA>100)
  } else if (grepl(habremove, pattern=",")){
    habremove<-stringr::str_split(habremove, pattern =",") %>% unlist() %>% trimws()
    
    poly_clean<-polygons%>%
      dplyr::filter(AREA>100)%>%
      dplyr::filter(!HABITAT %in% habremove)
    
  } else {
    habremove<-habremove
    
    poly_clean<-polygons%>%
      dplyr::filter(AREA>100)%>%
      dplyr::filter(!HABITAT %in% habremove)
  }
  
  #Make geometries valid 
  poly_clean<-poly_clean%>%st_make_valid()
  
  #Remove area column
  poly_clean<-poly_clean%>%select(-AREA)
  
  #Write out processed spatial framework
  sf_name<-basename(sf)
  sf::st_write(poly_clean, file.path(paste0(outpath, sf_name)))
  
}

#Iterate over Living England 
files<-list.files("./PhaseIV_Final_byBGZ/", full.names = T, pattern=".shp$")
out<-purrr::map(files, .f = process_sf)

#################### Make shapefile mapping with ARD frame ##########################

# read in BGZ extent shapefile
zones<-st_read("./LivingEngland/LivingEngland_BioGeographicZones_Phase4/LivingEngland_BioGeographicZones_Phase4.shp")%>%
  dplyr::select(Zone, geometry)

ard<-st_read("J:/GISprojects/EOMonitoringApplications/Sentinel-2_Grid/Sentinel-2-GB.shp")%>%st_transform(crs = st_crs(zones))%>%
  dplyr::select(Name, geometry)

# find intersection between 
intersect_df<-st_intersection(ard, zones)%>%st_drop_geometry()%>%mutate(framework = "liveng1")
intersect_order<-intersect_df[order(intersect_df$Zone),]

# change zones 13 and 14 to "1314" as only one shapefile covers both zones 13 and 14
intersect_order<-intersect_order%>%
  mutate(Zone = as.character(Zone))%>%
  mutate(Name = as.character(Name))%>%
  mutate(Zone = str_replace_all(Zone, c("^13$" = "1314", "^14$"= "1314")))

#write out as json
json<-rjson::toJSON(unname(split(intersect_order, 1:nrow(intersect_order))))
jsonlite::write_json(json, "./LivingEngland/ard_zones_s2.json")

################ Match polygons to Sentinel frame #########################

s2map<-"J:/GISprojects/EOMonitoringApplications/Sentinel-2_Grid/Sentinel-2-GB.shp"

#Get S2 granule map 
s2_frames<-sf::st_read(s2map)

#Assign outpath
outpath<-"./"

## Make function to iterate through liveng chunks and assign frame ID to polygons ##

assign_ID<-function(sf){

  #Set up dataframe to write results to 
  results<-NULL

  poly_clean<-sf::st_read(sf, stringsAsFactors= F)
  
  #Match crs of polygons and granule file 
  s2_frames <- s2_frames %>% sf::st_transform(s2_frames,crs=sf::st_crs(poly_clean))

  #Iterate through granules

  for (i in 1:nrow(s2_frames)){
  
    overlap<-sf::st_join(s2_frames[i,],poly_clean, join=st_contains, left=TRUE)
  
    #Extract polygons completely within the granule
    if (is.na(overlap$POLYID)){
      polys<-NA
    } else if (!is.na(overlap$POLYID)){
      polys<-toString(unique(overlap$POLYID))
    }
  
    #Extract granule ID
    granID<-as.character(unique(overlap$Name))
  
    #Put results together as array
    out<-data.frame(FrameID = granID,
                    POLYID = c(polys))
  
    results<-rbind(results,out)
  }

  frame_polyIDs<-results[complete.cases(results$POLYID),]

  ##Write json of frame IDs with array of matching polygon IDs
  frame_json<-rjson::toJSON(unname(split(frame_polyIDs, 1:nrow(frame_polyIDs))))

  filename<-tools::file_path_sans_ext(basename(sf))
  write(frame_json, file.path(paste0(outpath, filename, ".json")))

}

### Iterate over shapefile chunks 
files<-list.files("./LivingEngland/liveng1_zones_processed/", full.names = T, pattern = ".shp")

purrr::map(files, .f = assign_ID)


############################## Sentinel 1 #################################################

#################### Make shapefile mapping with ARD frame ##########################

# read in BGZ extent shapefile
zones<-st_read("./LivingEngland/LivingEngland_BioGeographicZones_Phase4/LivingEngland_BioGeographicZones_Phase4.shp")%>%
  dplyr::select(Zone, geometry)

ard<-st_read("Z:/Prog706-EcosystemsAnalysis/Defra NCEA/J2_EO_ChangeDetection/England_processing/S1_reframing/OSGB100kmGrid_BNG_buffered.shp")%>%st_transform(crs = st_crs(zones))%>%
  dplyr::select(gridref, geometry)

# find intersection between 
intersect_df<-st_intersection(ard, zones)%>%st_drop_geometry()%>%mutate(framework = "liveng1")
intersect_order<-intersect_df[order(intersect_df$Zone),]

# change zones 13 and 14 to "1314" as only one shapefile covers both zones 13 and 14
intersect_order<-intersect_order%>%
  mutate(Zone = as.character(Zone))%>%
  rename(Name = gridref)%>%
  mutate(Name = as.character(Name))%>%
  mutate(Zone = str_replace_all(Zone, c("^13$" = "1314", "^14$"= "1314")))
  
#write out as json
json<-rjson::toJSON(unname(split(intersect_order, 1:nrow(intersect_order))))
jsonlite::write_json(json, "./LivingEngland/ard_zones_s1.json")

################ Match polygons to Sentinel frame #########################

s1map<-"Z:/Prog706-EcosystemsAnalysis/Defra NCEA/J2_EO_ChangeDetection/England_processing/S1_reframing/OSGB100kmGrid_BNG_buffered.shp"

#Get S1 frame map 
s1_frames<-sf::st_read(s1map)

#Assign outpath
outpath<-"./"

## Make function to iterate through liveng chunks and assign frame ID to polygons ##

assign_ID<-function(sf){
  
  #Set up dataframe to write results to 
  results<-NULL
  
  poly_clean<-sf::st_read(sf, stringsAsFactors= F)
  
  #Match crs of polygons and granule file 
  s1_frames <- s1_frames %>% sf::st_transform(s1_frames,crs=sf::st_crs(poly_clean))
  
  #Iterate through granules
  
  for (i in 1:nrow(s1_frames)){
    
    overlap<-sf::st_join(s1_frames[i,],poly_clean, join=st_contains, left=TRUE)
    
    #Extract polygons completely within the granule
    if (is.na(overlap$POLYID)){
      polys<-NA
    } else if (!is.na(overlap$POLYID)){
      polys<-toString(unique(overlap$POLYID))
    }
    
    #Extract granule ID
    granID<-as.character(unique(overlap$gridref))
    
    #Put results together as array
    out<-data.frame(FrameID = granID,
                    POLYID = c(polys))
    
    results<-rbind(results,out)
  }
  
  frame_polyIDs<-results[complete.cases(results$POLYID),]
  
  ##Write json of frame IDs with array of matching polygon IDs
  frame_json<-rjson::toJSON(unname(split(frame_polyIDs, 1:nrow(frame_polyIDs))))
  
  filename<-tools::file_path_sans_ext(basename(sf))
  write(frame_json, file.path(paste0(outpath, filename, "_s1.json")))
  
}

### Iterate over shapefile chunks 
files<-list.files("./LivingEngland/liveng1_zones_processed/", full.names = T, pattern = ".shp")

purrr::map(files, .f = assign_ID)
