import rasterio
import argparse
import os
import pandas as pd
from datetime import date, datetime
import rio_cogeo
import multiprocessing as mp
import math

pd.set_option('display.max_rows', 2000) # make sure all rows are printed for QC check
# useage
# python indices_qc.py -d 2021-04-01 2021-04-11
# note date format is year/month/day


def run(startdate, enddate, inputdir, outputdir, arddir):
    print(f"Running QC for files in {inputdir} between dates {startdate} and {enddate}")
    lsdict = []
    indexs = ['NBR', 'NDMI', 'NDVI', 'NDWI']

    date_df = pd.date_range(start=startdate, end=enddate)
    lsdates = date_df.strftime('%Y/%m/%d').tolist()
    outputpath = os.path.join(outputdir, f'{startdate}_{enddate}_QC.csv')

    lsfilepaths = []
    for date in lsdates:
        for ind in indexs:
            filein = f"{ind.lower()}/{date}"
            fullpath = os.path.join(inputdir, filein)
            lsfilepaths.append(fullpath)

    for lsfilepath in lsfilepaths:
        if os.path.exists(lsfilepath):
            for file in os.listdir(lsfilepath):
                if file.endswith(".tif"):
                    filename = os.path.join(lsfilepath, file)
                    print(f"QCing file {filename}")
                    
                    # determine if tif file is an index
                    filesize = get_size(filename)
                    if any((match := substring) in file for substring in indexs):
                        index = match
                    else:
                        index = 'NA'
                    
                    file_splitter = filename.split('/')[-4:]

                    filepath_joiner = f'{arddir}/{file_splitter[0]}/{file_splitter[1]}/{file_splitter[2]}/{file_splitter[3]}'

                    # figure out the name of the source ard file
                    if filepath_joiner.endswith('_NBR.tif'):
                        ardfilename = f'{filepath_joiner[:-8]}_sat.tif'
                    else:
                        ardfilename = f'{filepath_joiner[:-9]}_sat.tif'
                    ardpath = os.path.normpath(ardfilename)
                    if os.path.exists(lsfilepath):
                        print(f'associated ARD file {ardpath}')
                        
                        # create a data row for this file
                        tuple_data = (filename, filesize, index, file, ardpath)
                        lsdict.append(tuple_data)
                    else: 
                        print(f'associated ARD file {ardpath} NOT FOUND')
                        
    # run tests in parallel for each row in lsdict
    #pool = mp.Pool(mp.cpu_count()) # perhaps if you want to speed up - but JASMIN might complain
    pool = mp.Pool(4)
    results = pool.map(multi_run_wrapper, lsdict)

    # print results of the tests 
    df = pd.DataFrame.from_dict(results)
    df['Check'] = df.index.isin(df.sample(frac=0.05, random_state=1).index) # 5% check
    df.to_csv(outputpath, index=False)
    print("---------------")
    print(f"Finished QC - CSV report saved to {outputpath}")
    print("---------------")
    print(f"Checking QC report")
    print(f"{len(df)} files QC")
    print(df.tile.value_counts())
    print("---------------")
    if len(df['crs'].unique()) == 1:
        print(f"CRS is consistent over all files: {df['crs'].unique()}")
    else:
        print(f"issue with CRS consistency, check QC file")
    if len(df['dtype'].unique()) == 1:
        print(f"data type is consistent over all files: {df['dtype'].unique()}")
    else:
        print(f"issue with data type consistency, check QC file")
    if len(df['within_range'].unique()) == 1:
        print(f"index range is consistent over all files: {df['within_range'].unique()}")
    else:
        print(f"issue with index range consistency, check QC file")
    if len(df['valid_cog'].unique()) == 1:
        print(f"All files are valid COGS")
    else:
        print(f"issue with one or more COGS, check QC file")
    if len(df['nodata'].unique()) == 1:
        print(f"All files have the same nodata value")
    else:
        print(f"Inconsistent no data values, check QC file")
    if len(df['extent_match'].unique()) == 1:
        print(f"All files have the same extent")
    else:
        print(f"Inconsistent extent, check QC file")
    if len(df['aligned'].unique()) == 1:
        print(f"All files are pixel aligned")
    else:
        print(f"Inconsistent pixel alignement, check QC file")
    print(f"Checking QC report finished")


def multi_run_wrapper(args):
    return get_stats(*args)

def get_size(path):
    # https://stackoverflow.com/questions/6080477/how-to-get-the-size-of-tar-gz-in-mb-file-in-python
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024*1024:
        return f"{round(size/1024, 2)} KB"
    elif size < 1024*1024*1024:
        return f"{round(size/(1024*1024), 2)} MB"
    elif size < 1024*1024*1024*1024:
        return f"{round(size/(1024*1024*1024), 2)} GB"


def get_stats(filename_path, filesize, index, file, ardfilename):
    filename_parts = filename_path.split('_')
    
    # determine if the file is a valid cog
    valid_cog, _, _ = rio_cogeo.cog_validate(filename_path)
    
    with rasterio.open(filename_path) as dataset:
        meta = dataset.profile # width, hight, crs etc
        indexBounds = dataset.bounds # get boundary extent
        idt = dataset.transform # get transformation params
        image = dataset.read()
        if dataset.overviews(1):
            overview = True
        else:
            overview = False
        # Set all nodata values to 0
        image[image == meta['nodata']] = 0
        
        meta['min'] = image.min()
        meta['max'] = image.max()
        meta['path'] = filename_path
        meta['filesize'] = filesize
        meta['index'] = index
        meta['overview'] = overview
        meta['QC_date'] = date.today()
        datetime_ard = datetime.strptime(str(filename_parts[3]), '%Y%m%d')
        meta['ARD_date'] = datetime_ard
        
        
        # pixel values in range 
        if meta['min'] > -1 and meta['max'] < 1:
            meta['within_range'] = 'Y'
        else:
            meta['within_range'] = 'N'
            
        # title validitiy lenght check?? Do we care / regex
        if file.endswith('_NBR.tif'):  # assumes others are NDVI NDMI NDWI
            meta['tile'] = file[:-8]
        else:
            meta['tile'] = file[:-9]
            
        # cog check
        meta['valid_cog'] = valid_cog
        with rasterio.open(ardfilename) as arddataset:
            ardBounds = arddataset.bounds # get boundary extent
            adt = arddataset.transform # get transformation params
        
        # check the boundary and alignment match
        # using math.isclose to mitigate against very small ~0.00001 diffs
        
        if math.isclose(ardBounds[0], indexBounds[0]) and math.isclose(ardBounds[1], indexBounds[1]) and math.isclose(ardBounds[2], indexBounds[2]) and math.isclose(ardBounds[3], indexBounds[3]):

            meta['extent_match'] = 'Y'
            if math.isclose(idt[0], adt[0]) and math.isclose(idt[4], adt[4]):
                meta['aligned'] = 'Y'
           
            else:
                meta['aligned'] = 'N'
                
        else:
            meta['extent_match'] = 'N'
            meta['aligned'] = 'N'
            meta['indexbounds'] = indexBounds
            meta['ardbounds'] = ardBounds
        
        meta['ard_transform'] = adt
        meta['cell_size'] = (f'{idt[0]}, {idt[4]}') # writing cell size to file
        
        return meta


if __name__ == '__main__':
    # Create the parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        "-d",
        nargs=2,
        metavar=('start', 'end'),  # Describes each argument
        help="Search for files between start and end dates, e.g. 2021-01-01 2021-01-31",
    )
    parser.add_argument(
        "--inputdir",
        "-i",
        default="/gws/nopw/j04/defra_eo/public/change-detection/indices/sentinel_2/",
        help="The base input directory where indices files are stored"
    )
    parser.add_argument(
        "--outputdir",
        "-o",
        default="/gws/nopw/j04/defra_eo/data/output/change-detection/qc",
        help="The output directory in which to save the CSV output"
    )
    parser.add_argument(
        "--arddir",
        "-a",
        default="/neodc/sentinel_ard/data/sentinel_2",
        help="The root ard directory in used to test again ard files"
    )
    args = parser.parse_args()
    run(args.date[0], args.date[1], args.inputdir, args.outputdir, args.arddir)
