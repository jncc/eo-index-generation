##Making thumbnails for individual polygons based on polygon IDs 

# load packages
suppressPackageStartupMessages(
  suppressWarnings({
    require(sp)
    require(raster)
    require(sf)
    require(fs)
    require(dplyr)
    require(tibble)
    require(tmap)
  })
)

# set up command line arguments
# optList <- list(
#   optparse::make_option("--sf",type="character"), #path to segmentation polygon layer
#   optparse::make_option("--polyID",type="character"), #ID of selected polygon 
#   optparse::make_option("--idfield", type ="character"), # field in segmentation polygon layer relating to polygon ID
#   optparse::make_option("--inpath", type = "character"), # path to input image/index image path 
#   optparse::make_option("--index", type = "character"), # name of index (options = NDVI, NDWI, NDMI, RVI, RVIv, true_colour, false_colour)
#   optparse::make_option("--outpath", type = "character") # directory (with trailing slash) to write data to
# )
# cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# #Assign variables
# segmentation_polygon<-cmdargs$sf 
# satellite_image_path<-cmdargs$inpath
# indexID<-cmdargs$index
# polyID<-cmdargs$polyID
# idfield<-cmdargs$idfield
# outDir<-cmdargs$outpath

polyThumbs<-function(segmentation_polygon, satellite_image_path, indexID, polyID, idfield, outDir){

  #Read in polygons layer
  segmentation_polygon<-st_read(segmentation_polygon)
  
    # Crop spatial framework to individual polygon
    segPoly <- segmentation_polygon %>%
      dplyr::filter((!!as.name(idfield)) == (as.numeric(polyID))) 
    
    # Extract date from input satellite/index image name
    date<-satellite_image_path%>%stringr::str_extract(pattern = "_[0-9]{8}")%>%
      stringr::str_remove(pattern = "_")
    
    #Create bounding box function to shape thumbnails to square extent
    # Crop satellite image to individual polygon
    
    #' Square bounding box extent
    #'
    #' This function converts a rectangular extent to a square extent
    #' by making the shortest side equal to the longest side 
    #'
    #' @param bounding_box_extent extent, raster extent object
    #'
    #' @return extent, sqaure raster extent object
    #' @export
    #'
    #' @examples
    square_bounding_box_extent <- function(bounding_box_extent) {
      e <- bounding_box_extent
      xlen <- (e@xmax - e@xmin) / 2
      ylen <- (e@ymax - e@ymin) / 2
      if (xlen > ylen) {
        ymid <- e@ymin + ylen
        e@ymin <- ymid - xlen
        e@ymax <- ymid + xlen
      } else if (ylen > xlen) {
        xmid <- e@xmin + xlen
        e@xmin <- xmid - ylen
        e@xmax <- xmid + ylen
      }
      e
    }
    
    ## Generate thumbnails for polygons
    
    # Index level polygon thumbnail
    if(indexID %in% c("NDVI", "NDWI", "NDMI", "RVI", "RVIv")){
      
      satellite_image <- raster::raster(satellite_image_path)
      
      # get date_text
      date <- date %>%
        lubridate::ymd()
      
      # Match polygon sf object and satellite image CRS
      segPoly <- segPoly %>% sf::st_transform(raster::crs(satellite_image))
      
      # stop if raster stack and extent_layer are not in the same projection
        stopifnot(raster::compareCRS(satellite_image, segPoly))
        
        # Get raster cell resolution
          cell_resolution <- raster::xres(satellite_image)
          
        # get extent  
          bounding_box <- sf::st_bbox(segPoly)
          bounding_box_extent <- raster::extent(c(bounding_box$xmin - cell_resolution, 
                                                  bounding_box$xmax + cell_resolution, 
                                                  bounding_box$ymin - cell_resolution, 
                                                  bounding_box$ymax + cell_resolution))
        # make extent square
          bounding_box_extent <- square_bounding_box_extent(bounding_box_extent)
          
          
          satellite_image_polygon<-raster::crop(satellite_image, bounding_box_extent)
      
      # palette lookup
      lookup <- tibble::tribble(~index,~breaks,~palette,
                                "NDVI", seq(-1,1,by=0.2),terrain.colors(9,rev=T),
                                "NDWI",seq(-1,1,by=0.2),"Blues",
                                "NDMI",seq(-1,1,by=0.2),"Purples",
                                "RVI", seq(1,1.6,by=0.1),"viridis",
                                "RVIv",seq(0,4,by=0.2),"viridis")
      
      # turn off tmap messages
      tmap::tmap_options(show.messages = FALSE)
      
      indexbreak <- lookup %>% dplyr::filter(index==indexID)
      
      # create image
      image_polygon <- suppressWarnings(tmap::tm_shape(satellite_image_polygon) + 
                                          tmap::tm_raster(title = indexID, palette = unlist(indexbreak$palette),
                                                          style = "fixed",
                                                          breaks = unlist(indexbreak$breaks)) +
                                          tmap::tm_shape(segPoly) +
                                          tmap::tm_borders(lwd = 2, col = "black") +
                                          tmap::tm_credits(as.character(date), size = 2, col = "black", fontface = "bold", 
                                                           position = c(0.65, 0.01),bg.color='white',bg.alpha=0.5) +
                                          tmap::tm_legend(show = FALSE) +
                                          tmap::tm_layout(outer.margins = c(0, 0, 0, 0)) +
                                          tmap::tm_facets(free.scales = FALSE))
    
      # Generate true colour polygon thumbnails
    } else if (indexID == "true_colour"){
      
      satellite_image <- raster::brick(satellite_image_path)
      
      # get date_text
      date <- date %>%
        lubridate::ymd()
      
      # match spatial framework and input raster CRS
      segPoly <- segPoly %>% sf::st_transform(raster::crs(satellite_image))
      
      # stop if raster stack and extent_layer are not in the same projection
      stopifnot(raster::compareCRS(satellite_image, segPoly))
      
      # Get raster cell resolution
      cell_resolution <- raster::xres(satellite_image)
      
      # get extent  
      bounding_box <- sf::st_bbox(segPoly)
      bounding_box_extent <- raster::extent(c(bounding_box$xmin - cell_resolution, 
                                              bounding_box$xmax + cell_resolution, 
                                              bounding_box$ymin - cell_resolution, 
                                              bounding_box$ymax + cell_resolution))
      # make extent square
      bounding_box_extent <- square_bounding_box_extent(bounding_box_extent)
      
      
      satellite_image_polygon<-raster::crop(satellite_image, bounding_box_extent)
      
      #rgb image
      sat_img <- satellite_image_polygon[[1:3]]
      
      sat_img[sat_img>255]<-255
      
      # create rgb image thumbnail
      image_polygon <- suppressWarnings(tmap::tm_shape(sat_img) + 
                                          tmap::tm_rgb(r=3, b=1, g=2,max.value = 255) +
                                          tmap::tm_shape(segPoly) +
                                          tmap::tm_borders(lwd = 1, col = "black") +
                                          tmap::tm_credits(as.character(date),
                                                           size = 0.5, col = "black", fontface = "bold",
                                                           position = c(0.65, 0.01), bg.color='white', bg.alpha=0.5) + 
                                          tmap::tm_legend(show = FALSE) +
                                          tmap::tm_layout(outer.margins = c(0, 0, 0, 0))+
                                          tmap::tm_facets(free.scales = FALSE))
      
      
      # Generate s1 polygon thumbnails
    } else if (indexID == "false_colour"){
      
      # get satellite raster image
      satellite_image <- raster::brick(satellite_image_path)
      
      # get date_text
      date <- date %>%
        lubridate::ymd()
      
      # match spatial framework and input raster CRS
      segPoly <- segPoly %>% sf::st_transform(raster::crs(satellite_image))
      
      # stop if raster stack and extent_layer are not in the same projection
      stopifnot(raster::compareCRS(satellite_image, segPoly))
      
      # Get raster cell resolution
      cell_resolution <- raster::xres(satellite_image)
      
      # get extent  
      bounding_box <- sf::st_bbox(segPoly)
      bounding_box_extent <- raster::extent(c(bounding_box$xmin - cell_resolution, 
                                              bounding_box$xmax + cell_resolution, 
                                              bounding_box$ymin - cell_resolution, 
                                              bounding_box$ymax + cell_resolution))
      # make extent square using function
      bounding_box_extent <- square_bounding_box_extent(bounding_box_extent)
      
      
      satellite_image_polygon<-raster::crop(satellite_image, bounding_box_extent)
      
      # create image
      image_polygon <- suppressWarnings(tmap::tm_shape(satellite_image_polygon[[1]]) +
                                          tmap::tm_raster(palette = "Greys",
                                                          style = "fixed",
                                                          breaks = seq(-30,20,by=5),midpoint=0,n=10) +
                                          tmap::tm_shape(segPoly) +
                                          tmap::tm_borders(lwd = 2, col = "black") +
                                          tmap::tm_credits(as.character(date),
                                                           size = 2, col = "black", fontface = "bold",
                                                           position = c(0.65, 0.01), bg.color='white', bg.alpha=0.5) +
                                          tmap::tm_legend(show = F) +
                                          tmap::tm_layout(outer.margins = c(0, 0, 0, 0)) +
                                          tmap::tm_facets(free.scales = FALSE))
      
    
    }
      
      
    # save image
    # SEN2_20160420_lat54lon217_T30UWE_ORB037_msk
    # SEN2_20160420_lat54lon217_T30UWE_ORB037_msk_RDVI

    imgName <- satellite_image_path %>% basename() %>% tools::file_path_sans_ext()
    image_file_path <- ""
        
    # change resolution depending on thumbnail type
    if (indexID == "true_colour"){
      image_file_path <- file.path(outDir, paste0(imgName, "_true_colour_", polyID, ".png"))

      tmap::tmap_save(image_polygon, 
                      width = 450, height = 450,
                      image_file_path) 
      # edit brightness
      img_orig <- magick::image_read(image_file_path)
      # imagery processing 
      img_new <- img_orig %>% magick::image_contrast(sharpen=10 ) %>% # edit contrast
        magick::image_modulate(brightness = 140) #edit brightness
      #write out
      magick::image_write(img_new, image_file_path)

      
    } else if (indexID == "false_colour") {

      image_file_path <- file.path(outDir, paste0(imgName, "_false_colour_", polyID, ".png"))  

      tmap::tmap_save(image_polygon, 
                width = 6, height = 6,
                image_file_path) 

    } else {

      image_file_path <- file.path(outDir, paste0(imgName, "_", polyID, ".png"))

      tmap::tmap_save(image_polygon, 
                      width = 6, height = 6,
                      image_file_path) 
    }

    # return
    return(image_file_path) 
}


