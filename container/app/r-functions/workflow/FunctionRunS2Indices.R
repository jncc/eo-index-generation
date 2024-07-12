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
#   optparse::make_option("--inpath", type = "character"), # the path to the masked S2 granule
#   optparse::make_option("--outpath", type = "character"), # the directory (with trailing slash) to write outputs to
#   optparse::make_option("--nir", type = "numeric", default = 7), # the number of the NIR band
#   optparse::make_option("--r", type = "numeric", default = 3), # the number of the R band
#   optparse::make_option("--g", type = "numeric", default = 2), # the number of the G band
#   optparse::make_option("--b", type = "numeric", default = 1), # the number of the B band
#   optparse::make_option("--swir1", type = "numeric", default = 9), # the number of the SWIR1 band
#   optparse::make_option("--swir2", type = "numeric", default = 10), # the number of the SWIR2 band
#   optparse::make_option("--index", type = "character") # the index/indices to run - can be an unquoted comma separated list
# )
# cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# ## Assign variables
# nir <- cmdargs$nir
# r <- cmdargs$r
# g <- cmdargs$g
# b <- cmdargs$b
# swir1 <- cmdargs$swir1
# swir2 <-cmdargs$swir2
# imagepath <- cmdargs$inpath
# fileout_path <- cmdargs$outpath
# index<-cmdargs$index

runS2Indices<-function(filebasename, imagepath, fileout_path, index, r, g, b, nir, swir1, swir2){

  ## If a list of indices is supplied, split the list
  if(grepl(index, pattern = ",")){
    indices <- stringr::str_split(index, pattern = ",") %>% unlist() %>% trimws()
  } else {
    indices <- index
  }

  ## Create indices functions
  EVI_fun <- function(x){2.5*(((x[[nir]]/1000)-(x[[r]]/1000))/(((x[[nir]]/1000)+(6*(x[[r]]/1000))-(7.5*(x[[b]]/1000)))+1))}
  GLI_fun <- function(x){((2*x[[g]])-x[[r]]-x[[b]])/((2*x[[g]])+x[[r]]+x[[b]])}
  GNDVI_fun <- function(x){(x[[nir]]-x[[g]])/(x[[nir]]+x[[g]])}
  RDVI_fun <- function(x){(x[[nir]]-x[[r]])/(x[[nir]]+x[[r]])^0.5}
  SAVI_fun <- function(x){((x[[nir]]-x[[r]])/(x[[nir]]+x[[r]]+0.5))*(1+0.5)}
  SBL_fun <- function(x){(x[[nir]]-(2.4*x[[r]]))}
  RB_fun <- function(x){(x[[r]]/x[[b]])}
  RG_fun <- function(x){(x[[r]]/x[[g]])}
  Brightness_fun <- function(x){((x[[r]]+x[[g]]+x[[b]])/3)}
  NDVI_fun <- function(x){(x[[nir]]-x[[r]])/(x[[nir]]+x[[r]])}
  NBR_fun <- function(x){(x[[nir]]-x[[swir2]])/(x[[nir]]+x[[swir2]])}
  NDWI_fun <- function(x){(x[[g]]-x[[nir]])/(x[[g]]+x[[nir]])}
  NDMI_fun <- function(x){(x[[nir]]-x[[swir1]])/(x[[nir]]+x[[swir1]])}
  GRVI_fun <- function(x){x[[nir]]/x[[g]]}
  
  ## Create lookup table
  all_ind <- tibble::tribble(~name,~formula,
                            "EVI",  EVI_fun,
                            "GLI", GLI_fun,
                            "GNDVI",GNDVI_fun,
                            "RDVI", RDVI_fun,
                            "SAVI", SAVI_fun,
                            "SBL", SBL_fun,
                            "RB", RB_fun,
                            "RG",RG_fun,
                            "Brightness",Brightness_fun,
                            "NDVI",NDVI_fun,
                            "NBR",NBR_fun,
                            "NDWI",NDWI_fun,
                            "NDMI",NDMI_fun,
                            "GRVI",GRVI_fun
  )

  ## Filter to specified indices
  indi_tib <- all_ind %>% dplyr::filter(name %in% indices)

  index_list <- as.list(indi_tib$name)

    ## Iterate through indices calculations with input masked S2 granule 
  indices_rasters <- purrr::map(index_list, function(ind){

    # get file and indices function
    granule <- raster::brick(as.character(imagepath))
    indi_row <- indi_tib %>% dplyr::filter(name == ind)
    #run indices function over rasterbrick
    ind_out <- raster::calc(granule, fun=indi_row$formula[[1]])
    
    #set projection to EPSG 27700 and NoData value to -9999
    crs(ind_out)<-CRS(SRS_string = "EPSG:27700")
    NAvalue(ind_out) = -9999
    
    #write out indices layer
    indices_raster = file.path(fileout_path, paste0(filebasename, "_", as.character(indi_row$name), ".tif"))
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
