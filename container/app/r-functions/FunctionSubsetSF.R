# renv::activate()

# Load required packages
suppressPackageStartupMessages(
  suppressWarnings({
    require(magrittr)
    require(raster)
    require(sf)
  })
)

# ## Set up command line arguments
# optList <- list(
#   optparse::make_option("--sf", type = "character"), # path to the spatial framework .shp files
#   optparse::make_option("--framepoly", type = "character"), #path to reference json file of frame IDs with polygon IDs falling within frame 
#   optparse::make_option("--idfield", type = "character"), # name of the field in the spatial framework corresponding to polygon ID
#   optparse::make_option("--habfield", type = "character"), # name of the field in the spatial framework corresponding to habitat name
  
#   optparse::make_option("--intif", type = "character"), # either the S1 scene or the S2 masked granule
#   optparse::make_option("--dataarea", type = "character"), #path to data area mask (output of MaskGranule function), needed for s2 images but NULL for s1 frames
#   optparse::make_option("--outpath", type = "character"), # the directory (with trailing slash) to write outputs to
#   optparse::make_option("--s2img", type = "logical", default = T) # are we dealing with S2 (T) or S1 (F)
#   )
# cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# ##Assign variables
# sf<-cmdargs$sf
# framepoly<-cmdargs$framepoly
# idfield<-cmdargs$idfield
# habfield<-cmdargs$habfield
# intif<-cmdargs$intif
# dataarea<-cmdargs$dataarea
# outpath<-cmdargs$outpath
# s2img<-cmdargs$s2img 

subsetSF<-function(sf, framepoly, idfield, habfield, intif, dataarea, outpath, s2img){

  ## Read the input raster
  img <- raster::raster(intif)

  ## Extract the date from the raster layer name
  date <- names(img) %>% stringr::str_extract("[0-9]{8}")

  ## Extract the frame ID from the raster layer name
  ## e.g. S2A_20231001_latn572lonw0037_T30VVJ_ORB037_20231002083624_msk_1
  ## and S1A_20240107_132_asc_175011_175036_VVVH_G0_GB_OSGB_RTCK_SpkRL_TF_1
  if(s2img){
    frameID <- names(img) %>% 
      stringr::str_extract(pattern = "(?<=T)(.*?)(?=_ORB)") %>%
      stringr::str_extract(pattern = "[0-9]{2}[A-Z]{3}")
  } else {
    frameID<-names(img)%>%
      stringr::str_extract(pattern = "SpkRL_([A-Z]{2})", group = 1)
  }
  
  ##Find polygons within image frame
  frame_polyIDs<-jsonlite::fromJSON(framepoly)
  polys_match<-frame_polyIDs%>%dplyr::filter(FrameID == frameID)
  polys_str<-unlist(strsplit(polys_match$POLYID, split=", "))

  ## Read in the spatial framework polygons, subset by polygons within frame 
  polygons <- sf::st_read(sf, quiet = T) %>%
    dplyr::select(idfield, habfield) %>%
    dplyr::rename(POLYID = 1, HABITAT = 2) %>%
    dplyr::filter(POLYID %in% polys_str)

  #Make polyid numeric for rasterisation, and convert habitat to character
  polygons$POLYID<-as.numeric(as.character(polygons$POLYID))
  polygons$HABITAT<-as.character(polygons$HABITAT)
  
  ## Make sure CRS match
  polygons<-polygons%>%sf::st_transform(polygons,crs=crs(img))
  
  ## Filter polygons fully within the data extent of frame - s2 images only 
  if(s2img){
    img_data<-raster::raster(dataarea)
    data_extent<-stars::st_as_stars(img_data) %>% #converts img_data tif to stars_proxy object
      stars::st_as_stars(downsample = 0, url = attr(., "url"), envir = parent.frame())%>% #converts to stars object
      sf::st_as_sf(merge = T, na.rm = T) %>% # raster to polygons 
      sf::st_transform(crs = crs(polygons))%>%
      sf::st_make_valid() #make sure geometries are valid 
    
    polygons<-sf::st_filter(polygons, data_extent, .predicate = st_within)
  }
  
  ## Only continue with the rest of the script if polygons are present in the data area
  if(nrow(polygons) > 0){
    
    ## Set up a raster template
    rtemplate <-raster::raster(crs=raster::crs(polygons),
                               res=raster::res(img),
                               ext=raster::extent(img))
    
    ## Rasterise the polygons
    poly_tif <- fasterize::fasterize(polygons, rtemplate, field = "POLYID")
    
    ## ID which polygons overlap NAs
    ## Find rows with NAs and extract polygon ID
    all_layers <- append(img, poly_tif)
    all_layers_df <- raster::as.data.frame(raster::stack(all_layers))
    na_row <- all_layers_df %>% 
      dplyr::filter(!is.na(layer) & !complete.cases(all_layers_df)) %>% 
      dplyr::select(layer) %>% 
      dplyr::pull() %>% 
      unique() 
    
    ## Filter polygon sf to remove polygons over NA values 
    polygons_filt<-polygons[!polygons$POLYID %in% na_row, ]
    
    ## Change POLYID type back to character 
    polygons_filt$POLYID<-as.character(polygons_filt$POLYID)
    
    ## Set up the output file name
    if(s2img){
      outName <- intif %>%
        basename() %>%
        tools::file_path_sans_ext()
    } else {
      outName <- basename(intif) %>%
        tools::file_path_sans_ext() %>%
        stringr::str_extract("^.+(?=_OSGB)")
    }
    
    ## Only write outputs if polygons present in poly_tif (ie polygons outside NA areas) 
    
    if ((dplyr::n_distinct(all_layers_df$layer, na.rm=T)) != (length(na_row))){
      
      ## Write the filtered polygon layer 
      shapeFile <- file.path(outpath, paste0(outName, "_poly.shp"))
      sf::st_write(polygons_filt, shapeFile, overwrite = T, append=F)
      
      
      output <- list(shapeFile = shapeFile, 
                     polygonCount = length(unique(polygons_filt$POLYID)))
      
      jsonOut <- rjson::toJSON(output)
      
      return(jsonOut)
    } else {
      output <- list(shapeFile = "", 
                     polygonCount = 0)
      
      jsonOut <- rjson::toJSON(output)
      
      return(jsonOut)
    }
    
  } else {
    output <- list(shapeFile = "", 
                   polygonCount = 0)
    
    jsonOut <- rjson::toJSON(output)
    
    return(jsonOut)
  }
}

