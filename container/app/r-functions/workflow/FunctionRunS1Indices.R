# renv::activate()

# Load required packages
suppressPackageStartupMessages(
  suppressWarnings({
    require(magrittr)
    require(raster)
  })
)

# # set up command line arguments
# optList <- list(
#   optparse::make_option("--inpath", type = "character"), # the path to the S1 scene
#   optparse::make_option("--outpath", type = "character"), # the directory (with trailing slash) to write outputs to
#   optparse::make_option("--vv", type = "numeric", default = 1), # the number of the VV band
#   optparse::make_option("--vh", type = "numeric", default = 2), # the number of the VH band
#   optparse::make_option("--index", type = "character") # the index/indices to run - can be an unquoted comma separated list
#   optparse::make_option("--threshold", type="numeric") # the numeric threshold to use to mask outliers, expects single number and uses the positive and negative value for the upper and lower thresholds, default = 5
# )
# cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# ## Assign variables
# imagepath <- cmdargs$inpath
# fileout_path <- cmdargs$outpath
# vv <- cmdargs$vv
# vh <- cmdargs$vh
# index<-cmdargs$index
# threshold<-cmdargs$threshold


runS1Indices<-function(filebasename, imagepath, fileout_path, vv=1, vh=2, index, threshold=50){
  if(grepl(index, pattern = ",")){
    index <- stringr::str_split(index, pattern = ",") %>% unlist() %>% trimws()
  } else {
    index <- index
  }

  ## Create indices functions

  ## Compute RVI using linear values.
  RVI_fun <- function(x){
    #Convert from db to linear
    VH_linear <- 10^(x[[vh]]/10)
    VV_linear <- 10^(x[[vv]]/10)
    rvi <- (4*VH_linear)/(VV_linear + VH_linear)
    return(rvi)
  }

  # Compute VV/VH using dB values
  VVVH_fun <- function(x){
    vvvh <- (x[[vv]]/x[[vh]])
    return(vvvh)
  }

  # Compute VH/VV using dB values
  VHVV_fun <- function(x){
    vhvv <- (x[[vh]]/x[[vv]])
    return(vhvv)
  }
 
  # Compute RFDI using linear values
  RFDI_fun <- function(x){
    #Convert from db to linear
    VH_linear <- 10^(x[[vh]]/10)
    VV_linear <- 10^(x[[vv]]/10)
    rfdi <- (VV_linear-VH_linear)/(VV_linear+VH_linear)
    return(rfdi)
  }

  ## Create lookup table
  all_ind <- tibble::tribble(~name,~formula,
                             "RVI", RVI_fun,
                             "VVVH", VVVH_fun,
                             "VHVV", VHVV_fun,
                             "RFDI", RFDI_fun)

  ## Filter to specified indices
  indi_tib <- all_ind %>% dplyr::filter(name %in% index)

  index_list <- as.list(indi_tib$name)
  
  ## Iterate through indices calculations with single input S1 scene
  indices_rasters <- purrr::map(index_list, function(ind){

    # Get file and indices function
    granule <- raster::brick(as.character(imagepath))
    indi_row <- indi_tib %>% dplyr::filter(name == ind)
    # Run indices function over raster
    ind_out <- raster::calc(granule, fun=indi_row$formula[[1]])
    
    # Mask outlier values specified by threshold to NA 
    ind_out[ind_out >= threshold] <- NA
    ind_out[ind_out <= (-threshold)] <- NA
    
    #set projection to EPSG 27700 and NoData value to -9999
    crs(ind_out)<-CRS(SRS_string = "EPSG:27700")
    NAvalue(ind_out) = -9999
    
    # Write out indices layer
    indices_raster <- file.path(fileout_path, paste0(filebasename, "_", as.character(indi_row$name), ".tif"))

    raster::writeRaster(ind_out,
                        indices_raster,
                        overwrite=T, NAflag = -9999, options = "COMPRESS=LZW")

    output <- list(indexName = indi_row$name,
        indexFile = indices_raster)

    return(output)
  })

  jsonOut <- rjson::toJSON(indices_rasters)

  return(jsonOut)
}
