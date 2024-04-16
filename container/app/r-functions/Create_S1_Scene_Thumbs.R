##Function to create S1 thumbnails for single S1 scene/area
# renv::activate()

# load packages
suppressPackageStartupMessages(
  suppressWarnings({
    require(sp)
    require(raster)
    require(stringr)
    require(dplyr)
    require(tibble)
    require(tmap)
  })
)

# # set up command line arguments
# optList <- list(
#   optparse::make_option("--inpath", type = "character"), # path to S1 scene raster file 
#   optparse::make_option("--indices", type = "character"), # path to indices raster file
#   optparse::make_option("--outpath", type = "character"), # path to save thumbnail png files 
#   optparse::make_option("--tmppath", type="character") # path to save temporary files in false colour thumbnail generation
# )
# cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# #Assign variables
# scene<-cmdargs$inpath
# indices<-cmdargs$indices
# outpath<-cmdargs$outpath
# tmppath<-cmdargs$tmppath

s1thumbs<-function(scene, rviTif, rvivTif, outpath){
  
  #Create brick of input S1 scene
  s1_lyr <- raster::brick(scene)
  
  #Get image ID 
  fileNamePrefix <- basename(granule) %>% stringr::str_remove('.tif')

  # imgfile <- basename(scene) %>%
  #   tools::file_path_sans_ext() %>%
  #   stringr::str_extract("^.+(?=_OSGB)")
  
  #Get date
  date <- stringr::str_extract(scene, pattern="(?<=_)[0-9]{8}(?=_)")
  
  #stack indices
  ind_stack <- list(rvi=raster::raster(rviTif),
                    rviv=raster::raster(rvivTif))
  
  # create index thumbnails
  indices_thumbs<-purrr::map(ind_stack,.f=function(thumbs){
    strindex <- stringr::str_split(names(thumbs),"_")

    indexname <- strindex[[1]][length(strindex[[1]])]

    #mapping lookup
    lookup <- tibble::tribble(~index,~breaks,
                              "RVI", seq(0,2,by=0.1),
                              "RVIv",seq(0,5,by=0.2))
    indexbreak <- lookup %>% dplyr::filter(index==indexname)

    tmap::tmap_options(show.messages = FALSE)

    image_thumbnail <- tmap::tm_shape(thumbs) +
      tmap::tm_raster(palette = "viridis",
                      style = "fixed",
                      breaks = unlist(indexbreak$breaks)) +
      tmap::tm_credits(paste0(as.character(date),"_",indexname), size = 1, col = "black", fontface = "bold",
                        position = c(0.7, 0.01)) +
      tmap::tm_legend(show = FALSE) +
      tmap::tm_layout(outer.margins = c(0, 0, 0, 0))
    indicesThumbFile = file.path(outpath, paste0(fileNamePrefix, "_",indexname,'.png'))
    tmap::tmap_save(image_thumbnail,filename = indicesThumbFile),width = 6, height = 6)

    return(indicesThumbFile)
  })
                    
  # create s1 false colour thumbnails
  image<-raster::raster(scene,band=1)
  raster::writeRaster(image, paste0(tmppath,as.character(date),'_temp_band1.tif'))
  image<-raster::raster(paste0(tmppath,as.character(date),'_temp_band1.tif'))
    ## plot thumbnail
    image_thumbnail <- tmap::tm_shape(image) +
    tmap::tm_raster(palette = "Greys",
                    style = "fixed",
                    breaks = seq(-30,20,by=5),midpoint=0,n=10) +
      tmap::tm_credits(paste0(as.character(date),"_S1"), size =1, col = "black", fontface = "bold",
                           position = c(0.7, 0.01)) +
      tmap::tm_legend(show = F) +
      tmap::tm_layout(outer.margins = c(0, 0, 0, 0)) +
      tmap::tm_facets(free.scales = FALSE)
    #save out
    falseColourThumbFile = file.path(outpath, paste0(fileNamePrefix, '_FalseColour.png'))
    suppressWarnings(tmap::tmap_save(image_thumbnail,filename = falseColourThumbFile), width = 6, height = 6))

  output <- list(
    falseColourThumbnail = falseColourThumbFile,
    indicesThumbnails = indices_thumbs
  )

  json <- rjson::toJSON(output)    

  return(json)      
                    
}

