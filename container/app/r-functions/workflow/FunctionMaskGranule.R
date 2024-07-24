# renv::activate()

# load required packages
suppressPackageStartupMessages(
  suppressWarnings({
    require(magrittr)
    require(raster)
    require(sf)
  })
)

maskGranule <- function(imgfile, cloudfile, topofile, workingFolder){
  # cloud and shadow masking
  satellite <- raster::stack(imgfile)
  cloud <- raster::raster(cloudfile)
  shadow <- raster::raster(topofile)
  
  # crop to ard extent
  satellite_extent <- raster::extent(satellite)
  cropped_cloud <- raster::crop(cloud, satellite_extent)
  
  # cloud mask
  satellite_msk <- raster::overlay(satellite, cropped_cloud, fun = function(x, y){
    x[!is.na(y[])] <- NA
    return(x)
  })
  
  # shadow mask
  satellite_msk <- raster::overlay(satellite_msk, shadow, fun = function(x, y){
    x[!is.na(y[])] <- NA
    return(x)
  })
  
  # ensure same projection as input file
  crs(satellite_msk)<-raster::crs(satellite)
  
  # get name
  outName <- basename(imgfile) %>% 
    tools::file_path_sans_ext() %>%
    stringr::str_extract(pattern = "^.+(?=_utm)")
  
  outfile <- file.path(workingFolder, paste0(outName, "_msk.tif"))
  
  # write raster
  raster::writeRaster(satellite_msk,
                      outfile,
                      overwrite=T, options = "COMPRESS=LZW")
  
  
  # Extract data area of raster image
  img_data<-raster::raster(imgfile)
  img_data[!is.na(img_data[])]<-1
  
  # Write raster of data area
  data_area_outfile<-file.path(workingFolder, paste0(outName, "_data_area.tif"))
  raster::writeRaster(img_data, data_area_outfile, overwrite=T, options = "COMPRESS=LZW")
  
  #List outputs
  output <- list(maskedArdFile = outfile,
                 dataAreaMask = data_area_outfile)
  
  jsonOut <- rjson::toJSON(output)
  
  return(jsonOut)
  
}


