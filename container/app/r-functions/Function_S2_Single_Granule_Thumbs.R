##Function to create whole granule S2 thumbnails  (running one selected image at a time)
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
#   optparse::make_option("--inpath", type = "character"), # path to masked S2 granule raster file 
#   optparse::make_option("--indices", type = "character"), # path to indices raster file
#   optparse::make_option("--outpath", type = "character") # path to save thumbnail png files 
# )
# cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# #Assign variables
# granule<-cmdargs$inpath
# indices<-cmdargs$indices
# outpath<-cmdargs$outpath

granThumbs<-function(granule, ndvi, ndwi, ndmi, outpath){

  #Create brick of input masked S2 granule
  satellite_msk <- raster::brick(granule)

  #Get masked image ID 
  imgfile <- stringr::str_extract(granule, pattern= "SEN2.*")
  
  #get date
  date <- stringr::str_extract(granule, pattern="(?<=_)[0-9]{8}(?=_)")

  #stack indices
  ind_stack <- list(ndvi=raster::raster(ndvi),
                  ndwi=raster::raster(ndwi),
                  ndmi=raster::raster(ndmi))

  ## Create thumbnails
  #Indices
  
  fileNamePrefix <- basename(granule) %>% stringr::str_remove('_msk.tif')

  indices_thumbs<-purrr::map(ind_stack,.f=function(thumbs){
    strindex <- stringr::str_split(names(thumbs),"_")
    indexname <- strindex[[1]][length(strindex[[1]])]
    #mapping lookup
    lookup <- tibble::tribble(~index,~breaks,~palette,
                              "NDVI", seq(-1,1,by=0.2),terrain.colors(9,rev=T),
                              "NDWI",seq(-1,1,by=0.2),"Blues",
                              "NDMI",seq(-1,1,by=0.2),"Purples")
    indexbreak <- lookup %>% dplyr::filter(index==indexname)
    tmap::tmap_options(show.messages = FALSE)
    image_thumbnail <- tmap::tm_shape(thumbs) +
      tmap::tm_raster(palette = unlist(indexbreak$palette),
                      style = "fixed",
                      breaks = unlist(indexbreak$breaks),midpoint=0,n=10) +
      tmap::tm_credits(paste0(as.character(date)), size = 2, col = "black", fontface = "bold",
                       position = c(0.65, 0.01),bg.color='white',bg.alpha=0.5) +
      tmap::tm_legend(show = F) +
      tmap::tm_layout(outer.margins = c(0, 0, 0, 0)) +
      tmap::tm_facets(free.scales = FALSE)

    indicesThumbFile = file.path(outpath, paste0(fileNamePrefix,'_', indexname,'.png'))

    tmap::tmap_save(image_thumbnail,filename = indicesThumbFile, width = 6, height = 6)

    return(indicesThumbFile)
  })

  #rgb image
  sat_img <- satellite_msk[[1:3]]
  sat_img[sat_img>255]<-255
  rgb_thumb <- suppressWarnings(tmap::tm_shape(sat_img) + tmap::tm_rgb(r=3, b=1, g=2,max.value = 255) +
                                  tmap::tm_credits(paste0(as.character(date)), size = 0.5, col = "black", fontface = "bold",
                                                   position = c(0.65, 0.01),bg.color='white',bg.alpha=0.5) + 
                                  tmap::tm_layout(outer.margins = c(0, 0, 0, 0)))
  
  
  rgbThumbFile = file.path(outpath, paste0(fileNamePrefix,'_RGB.png'))

  suppressWarnings(tmap::tmap_save(rgb_thumb,filename = rgbThumbFile, width = 450, height = 450))

  output <- list(
    rgbThumbnail = rgbThumbFile,
    indicesThumbnails = indices_thumbs
  )

  json <- rjson::toJSON(output)    

  return(json)
}  