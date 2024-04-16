renv::init()
require(dplyr)
require(magrittr)
require(raster)
require(optparse)
require(stringr)
require(fasterize)
require(rjson)
require(sf)
require(lubridate)
require(zoo)
require(tmap)
require(rgdal)
sessionInfo()

#attached base packages:
#  [1] stats     graphics  grDevices utils     datasets  methods   base     

#other attached packages:
#  [1] rgdal_1.4-8     tmap_3.0        zoo_1.8-6       lubridate_1.7.4 sf_0.9-5        rjson_0.2.20    fasterize_1.0.3 stringr_1.4.0  
#[9] optparse_1.6.6  magrittr_1.5    raster_3.3-13   sp_1.4-2        dplyr_0.8.3    

#loaded via a namespace (and not attached):
#  [1] tidyselect_1.1.0   purrr_0.3.3        lattice_0.20-38    vctrs_0.3.2        viridisLite_0.3.0  htmltools_0.4.0    stars_0.4-3       
#[8] getopt_1.20.3      base64enc_0.1-3    XML_3.99-0.3       rlang_0.4.8        e1071_1.7-3        pillar_1.4.4       later_1.0.0       
#[15] glue_1.3.1         DBI_1.0.0          RColorBrewer_1.1-2 htmlwidgets_1.5.1  codetools_0.2-16   leafsync_0.1.0     fastmap_1.0.1     
#[22] httpuv_1.5.2       crosstalk_1.0.0    parallel_3.6.1     class_7.3-15       fansi_0.4.0        leafem_0.1.3       Rcpp_1.0.3        
#[29] KernSmooth_2.23-16 xtable_1.8-4       promises_1.1.0     classInt_0.4-3     lwgeom_0.1-7       leaflet_2.0.3      abind_1.4-5       
#[36] mime_0.7           png_0.1-7          packrat_0.5.0      digest_0.6.23      stringi_1.4.3      shiny_1.4.0        tmaptools_3.1     
#[43] grid_3.6.1         cli_2.0.2          tools_3.6.1        tibble_2.1.3       dichromat_2.0-0    crayon_1.3.4       pkgconfig_2.0.3   
#[50] ellipsis_0.3.0     assertthat_0.2.1   rstudioapi_0.11    R6_2.4.1           units_0.6-5        compiler_3.6.1 

renv::snapshot()
