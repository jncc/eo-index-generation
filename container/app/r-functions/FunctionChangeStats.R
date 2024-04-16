renv::activate()

# load required packages
suppressPackageStartupMessages(
  suppressWarnings({
    require(magrittr)
    require(raster)
  })
)

# # set up command line arguments
# optList <- list(
#   optparse::make_option("--stats", type = "character"), # zonal stats file input (NEED TO DECIDE .txt OR DATABASE)
#   optparse::make_option("--sf", type = "character"), # filepath to the polygons spatial framework shapefile
#   optparse::make_option("--polyid", type = "character"), # the field in the polygon shapefile containing the polygon ID 
#   optparse::make_option("--habfield", type = "character"), # the field in the polygon shapefile containing the habitat class
#   optparse::make_option("--outpath", type = "character") # the directory (with trailing slash) to write outputs
# )
# cmdargs <- optparse::parse_args(optparse::OptionParser(option_list = optList))

# #Assign variables
# stats<-cmdargs$stats
# polygons<-cmdargs$sf
# polyid<-cmdargs$polyid
# habfield<-cmdargs$habfield
# outpath<-cmdargs$outpath



change_stats <- function(stats, outpath, polygons, polyid, habfield){

  #load in the files
  sitename <- gsub(basename(stats),pattern='_zonal_stats.txt',replacement='') ##NEED TO CHANGE THIS IF DATABASE
  zonaloutput <- read.csv(stats)
  polys <- sf::st_read(polygons,quiet=T) %>% sf::st_drop_geometry() %>% dplyr::select(polyid,habfield)

  #get indices names
  indices <- as.character(unique(zonaloutput$index))

  #iterate through indices
  purrr::map(indices, .f=function(ind){

    ## MONTHLY STATISTICS
    if(!dir.exists(paste0(outpath,'Monthly_statistics'))){
      dir.create(paste0(outpath,'Monthly_statistics'))
    }
    # group by month and year
    monthly <- zonaloutput %>% dplyr::filter(index==ind) %>%
      dplyr::group_by(ID,index,month, year) %>%
      dplyr::summarise(mean = mean(mean),sd = mean(sd),median = mean(median),
                       min = min(min),max = max(max),
                       Q1 = mean(Q1),Q3 = mean(Q3),
                       date= paste(date,collapse=','))
    #write out
    write.csv(monthly,paste0(outpath,"Monthly_statistics/",sitename,'_',ind,"_monthly_stats.txt"))


    ## MONTHLY CHANGE STATISTICS
    month_stat <- dplyr::left_join(monthly,polys,by=c('ID'=polyid)) %>%
      dplyr::ungroup()
    month_year <- month_stat %>%
      dplyr::mutate(month=ifelse(month<10,as.character(paste0("0",month)),as.character(month))) %>%
      dplyr::mutate(year=as.character(year)) %>%
      dplyr::mutate(monthname = stringr::str_glue("{year}-{month}")) %>%
      dplyr::mutate(monthdate = zoo::as.yearmon(monthname))

    mean_hab <- month_year  %>% dplyr::group_by(monthdate,get(habfield)) %>%
      dplyr::summarise(hab_mean=mean(mean),hab_meansd=sd(mean),hab_median=mean(median),hab_mediansd=sd(median),hab_min=mean(min),hab_minsd=sd(min),hab_max=mean(max),hab_maxsd=sd(max),hab_Q1=mean(Q1),hab_Q1sd=sd(Q1),hab_Q3=mean(Q3),hab_Q3sd=sd(Q3))
    write.csv(mean_hab,paste0(outpath,"Monthly_statistics/",sitename,'_',ind,'_monthly_changestats.txt'))


    ## SEASONAL STATISTICS
    if(!dir.exists(paste0(outpath,'Seasonal_statistics'))){
      dir.create(paste0(outpath,'Seasonal_statistics'))
    }
    # group by season
    season <-zonaloutput  %>% dplyr::filter(index==ind) %>%
      dplyr::group_by(ID,index,seasonyear) %>%
      dplyr::summarise(mean = mean(mean),sd = mean(sd),median = mean(median),
                       min = min(min),max = max(max),
                       Q1 = mean(Q1),Q3 = mean(Q3),
                       date= paste(date,collapse=','))
    #write out
    write.csv(season,paste0(outpath,"Seasonal_statistics/",sitename,'_',ind,"_seasonal_stats.txt"))

    ## SEASONAL CHANGE STATISTICS
    all_stat <- dplyr::left_join(season,polys,by=c('ID'=polyid))
    #calculate mean season stat per year per habitat type
    mean_hab <- all_stat %>%  dplyr::group_by(seasonyear,get(habfield)) %>%
      dplyr::summarise(hab_mean=mean(mean),hab_meansd=sd(mean),hab_median=mean(median),hab_mediansd=sd(median),hab_min=mean(min),hab_minsd=sd(min),hab_max=mean(max),hab_maxsd=sd(max),hab_Q1=mean(Q1),hab_Q1sd=sd(Q1),hab_Q3=mean(Q3),hab_Q3sd=sd(Q3))
    write.csv(mean_hab,paste0(outpath,"Seasonal_statistics/",sitename,'_',ind,"_seasonal_changestats.txt"))

    print(paste(ind, "done."))
  }) # close iteration

}
