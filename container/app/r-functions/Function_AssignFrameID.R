##Assign frame ID (equivalent to S2 granule ID)

suppressPackageStartupMessages(
  suppressWarnings({
    require(magrittr)
    require(raster)
    require(rgdal)
    require(sf)
  })
)

## Set up command line arguments
optList <- list(
  optparse::make_option("--sf", type = "character"), # path to the spatial framework .shp files
  optparse::make_option("--idfield", type = "character"), # name of the field in the spatial framework corresponding to polygon ID
  optparse::make_option("--habfield", type = "character"), # name of the field in the spatial framework corresponding to habitat name
  optparse::make_option("--habremove", type= "character"), # vector of habitats to remove - can be unquoted and comma separated list - if none then expects "NULL", default = NULL
  optparse::make_option("--s2map", type= "character"), # path to the folder containing S2 granule map 
  optparse::make_option("--outpath", type = "character"), # the directory (with trailing slash) to write outputs to
)
cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

#Assign variables
sf<-cmdargs$sf
idfield<-cmdargs$idfield
habfield<-cmdargs$habfield
habremove<-cmdargs$habremove
s2map<-cmdargs$s2map
outpath<-cmdargs$outpath

FramePolygonIDs<-function(sf, idfield, habfield, habremove, s2map, outpath){
  
  #Read in spatial framework and assign field names to variables
  polygons <- sf::st_read(sf, quiet = T) %>%
    dplyr::mutate(area_m = sf::st_area(geometry))%>%
    units::drop_units()%>%
    dplyr::select(idfield, habfield, area_m) %>%
    dplyr::rename(POLYID = 1, HABITAT = 2, AREA = 3)
  
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
  
  #Write out processed spatial framework
  sf_name<-tools::file_path_sans_ext(basename(sf))
  sf::st_write(poly_clean, file.path(paste0(outpath, sf_name, ".shp")))
  
  ##Match polygons to Sentinel frame 
  
  #Get S2 granule map 
  s2_frames<-sf::st_read(s2map)
  
  #Set up dataframe to write results to 
  results<-NULL
  
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

