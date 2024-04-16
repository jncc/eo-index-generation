##Making S2 thumbnails for whole sites based on a date - so running one selected image at a time

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

# set up command line arguments
optList <- list(
  optparse::make_option("--date", type = "character"), # date of image to search for masked file eg 20150708
  optparse::make_option("--inpath", type = "character"), # path to masked S2 granules raster files (with trailing /)
  optparse::make_option("--indices", type = "character"), # path to indices raster files
  optparse::make_option("--outpath", type = "character") # path to save thumbnail png files 
)
cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# list masked tifs and pull out data we need
s2masked <- data.frame(fls = list.files(cmdargs$inpath, full.names = F, pattern = "_msk.tif$"), stringsAsFactors = F) %>%
  dplyr::mutate(date = stringr::str_extract(fls, pattern = "(?<=_)[0-9]{8}(?=_)")) %>%
  dplyr::mutate(code = stringr::str_extract(fls, pattern = "(?<=_)[A-z]{1}[0-9]{2}[A-z]{3}_[A-z]{3}[0-9]{3}(?=_)"))

# get matching images
flsProc <- s2masked %>% 
  dplyr::filter(date==cmdargs$date) %>%
  dplyr::select(fls)

# id the masked image file
imgfile <- flsProc %>% 
  dplyr::filter(stringr::str_detect(fls, pattern="_msk")) %>% 
  dplyr::pull()

# if more than one imgfile per date use first
if(length(imgfile)>1){
  imgfile<-imgfile[1]
}

#Create brick of input masked S2 granules
satellite_msk <- raster::brick(paste0(cmdargs$inpath,imgfile))

#get date
date <- cmdargs$date

#stack indices
ind_stack <- list(ndvi=raster::raster(paste0(cmdargs$indices,tools::file_path_sans_ext(imgfile),"_NDVI.tif")),
                  ndwi=raster::raster(paste0(cmdargs$indices,tools::file_path_sans_ext(imgfile),"_NDWI.tif")),
                  ndmi=raster::raster(paste0(cmdargs$indices,tools::file_path_sans_ext(imgfile),"_NDMI.tif")))

## create thumbnails
#indices
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
  tmap::tmap_save(image_thumbnail,filename =  paste0(cmdargs$outpath,as.character(date),"_",indexname,'.png'),
                  width = 6, height = 6)
  
})
#rgb image
sat_img <- satellite_msk[[1:3]]
sat_img[sat_img>255]<-255
rgb_thumb <- suppressWarnings(tmap::tm_shape(sat_img) + tmap::tm_rgb(r=3, b=1, g=2,max.value = 255) +
                                tmap::tm_credits(paste0(as.character(date)), size = 0.5, col = "black", fontface = "bold",
                                                 position = c(0.65, 0.01),bg.color='white',bg.alpha=0.5) + 
                                tmap::tm_layout(outer.margins = c(0, 0, 0, 0)))
suppressWarnings(tmap::tmap_save(rgb_thumb,filename =  paste0(cmdargs$outpath,as.character(date),'_RGB.png'),
                                 width = 450, height = 450))
