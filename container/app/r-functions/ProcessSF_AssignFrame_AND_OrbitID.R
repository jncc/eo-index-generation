##Assign S2 granule and orbit

## Set up command line arguments
optList <- list(
  optparse::make_option("--sf", type = "character"), # path to the spatial framework .shp files
  optparse::make_option("--idfield", type = "character"), # name of the field in the spatial framework corresponding to polygon ID
  optparse::make_option("--habfield", type = "character"), # name of the field in the spatial framework corresponding to habitat name
  optparse::make_option("--habremove", type= "character"), # vector of habitats to remove - can be unquoted and comma separated list - if none then expects "NULL"
  optparse::make_option("--s2map", type= "character"), # path to the folder containing S2 granule/orbit map shapefiles
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
      dplyr::filter(AREA>=100)
  } else if (grepl(habremove, pattern=",")){
    habremove<-stringr::str_split(habremove, pattern =",") %>% unlist() %>% trimws()
    
    poly_clean<-polygons%>%
      dplyr::filter(AREA>=100)%>%
      dplyr::filter(!HABITAT %in% habremove)
    
  } else {
    habremove<-habremove
    
    poly_clean<-polygons%>%
      dplyr::filter(AREA>=100)%>%
      dplyr::filter(!HABITAT %in% habremove)
  }
  
  ##Match polygons to Sentinel frame 
  
  #Get list of S2 orbit/granule files 
  s2_orbits<-list.files(s2map, pattern=".shp")
  
  #Set up dataframe to write results to 
  all_orb_results<-NULL
  
  results<-NULL
  
  #Iterate through orbit files
  s2_IDmatch<-purrr::map_df(s2_orbits, function(orbit){
    
    #Get orbit ID
    orb<-as.character(stringr::str_extract(orbit, pattern="[0-9]{2,3}"))
    if (stringr::str_length(orb)==2){
      orb_ID<-paste0("0",orb)
    } else {
      orb_ID<-orb
    }
    
    #Read in orbit/granule shapefile
    orb_gran<-st_read(file.path(s2map,orbit))
    
    #Match crs of polygons and orb/granule file 
    polygons <- poly_clean %>% sf::st_transform(poly_clean,crs=st_crs(orb_gran))
    
    #Iterate through granules
    
    for (i in 1:nrow(orb_gran)){
      
      overlap<-st_join(orb_gran[i,],polygons, join=st_contains, left=TRUE)
      
      #Extract polygons completely within the granule
      if (is.na(overlap$POLYID)){
        polys<-NA
      } else if (!is.na(overlap$POLYID)){
        polys<-toString(unique(overlap$POLYID))
      }
      
      #Extract granule ID
      granID<-as.character(unique(overlap$Name))
      
      #Put results together as array
      out<-data.frame(OrbID = orb_ID,
                      GranID = granID,
                      OrbGran = paste0("T",granID,"_ORB", orb_ID),
                      POLYID = c(polys))
      
      results<-rbind(results,out)
    }
    
    
    all_orb_results<-rbind(all_orb_results, results)
    
  })
  
  frame_polyIDs<-s2_IDmatch[complete.cases(s2_IDmatch$POLYID),]
  
  ##Write json of frame IDs with array of matching polygon IDs
  frame_json<-rjson::toJSON(unname(split(frame_polyIDs, 1:nrow(frame_polyIDs))))
  
  write(frame_json, file.path(outpath, "frame_polyID.json"))
  
}

