import rasterio
import argparse
import os
import pandas as pd
from datetime import date, datetime
import rio_cogeo
import multiprocessing as mp
import math
import re

from qc.utils import get_size, get_logger
from qc.df_checks import *

logger = get_logger("indices_qc")

pd.set_option("display.max_rows", 2000)


def run(start_date, end_date, input_dir, output_dir, ard_dir):
    logger.info(f"Running QC for files in {input_dir} between dates {start_date} and {end_date}")
    ls_dict = []
    indices = ["NBR", "NDMI", "NDVI", "NDWI"]

    date_df = pd.date_range(start=start_date, end=end_date)
    ls_dates = date_df.strftime("%Y/%m/%d").tolist()
    output_path = os.path.join(output_dir, f"{start_date}_{end_date}_QC.csv")

    ls_file_paths = []
    for date in ls_dates:
        for ind in indices:
            file_in = f"{ind.lower()}/{date}"
            full_path = os.path.join(input_dir, file_in)
            ls_file_paths.append(full_path)

    for ls_file_path in ls_file_paths:
        if os.path.exists(ls_file_path):
            for file in os.listdir(ls_file_path):
                if file.endswith(".tif"):
                    filename = os.path.join(ls_file_path, file)
                    logger.info(f"QCing file: {filename}")

                    file_size = get_size(filename)
                    index = match if any((match := substring) in file for substring in indices) else "NA"

                    file_splitter = filename.split("/")[-4:]
                    filepath_joiner = f"{ard_dir}/{file_splitter[0]}/{file_splitter[1]}/{file_splitter[2]}/{file_splitter[3]}"

                    ardfilename = re.sub(fr"_({'|'.join(indices)}).tif$", "_sat.tif", filepath_joiner, flags=re.IGNORECASE)
                    ard_path = os.path.normpath(ardfilename)

                    logger.info(f">>> ARD file path: {filepath_joiner}")
                    if os.path.exists(ard_path):
                        logger.info(f">>> Associated ARD file: {ard_path}")

                        # Create a row for the data
                        tuple_data = (filename, file_size, index, file, ard_path)
                        ls_dict.append(tuple_data)
                    else:
                        logger.error(f">>> Associated ARD file not found: {ard_path}")

    pool = mp.Pool(4)
    results = pool.map(_multi_run_wrapper, ls_dict)

    process(results, output_path)


def _multi_run_wrapper(args):
    return get_stats(*args)


def get_stats(filename_path, file_size, index, file, ardfilename):

    # determine if the file is a valid cog
    valid_cog, _, _ = rio_cogeo.cog_validate(filename_path)

    with rasterio.open(filename_path) as dataset:
        meta = dataset.profile  # width, hight, crs etc
        indexBounds = dataset.bounds  # get boundary extent
        idt = dataset.transform  # get transformation params
        pixel = dataset.res  # get pixel size
        units = dataset.crs.linear_units  # get units of crs
        image = dataset.read()

        # Set all nodata values to 0
        image[image == meta["nodata"]] = 0

        meta["min"] = image.min()
        meta["max"] = image.max()
        meta["path"] = filename_path
        meta["filesize"] = file_size
        meta["index"] = index
        meta["overview"] = bool(dataset.overviews(1))
        meta["is_resolution_10"] = bool(pixel == (10.0, 10.0))
        meta["is_units_m"] = bool(units == "metre")
        meta["QC_date"] = date.today()
        meta["ARD_date"] = datetime.strptime(re.search(r".*_(\d{4}\d{2}\d{2})_.*", file).group(1), "%Y%m%d").date()
        meta["tile"] = re.sub(fr"_{index}.tif$", "", file, flags=re.IGNORECASE)

        meta["within_range"] = bool(meta["min"] > -1 and meta["max"] < 1)

        meta["valid_cog"] = valid_cog

        with rasterio.open(ardfilename) as arddataset:
            ardBounds = arddataset.bounds  # get boundary extent
            adt = arddataset.transform  # get transformation params

            if (math.isclose(ardBounds[0], indexBounds[0]) and
                math.isclose(ardBounds[1], indexBounds[1]) and
                math.isclose(ardBounds[2], indexBounds[2]) and
                    math.isclose(ardBounds[3], indexBounds[3])):

                meta["extent_match"] = True
                meta["aligned"] = bool(math.isclose(idt[0], adt[0]) and math.isclose(idt[4], adt[4]))

            else:
                meta["extent_match"] = False
                meta["indexbounds"] = indexBounds
                meta["ardbounds"] = ardBounds

        meta["ard_transform"] = adt
        meta["cell_size"] = f"{idt[0]}, {idt[4]}"  # writing cell size to file

        return meta


def process(results, output_path):
    df = pd.DataFrame.from_dict(results)
    df["Check"] = df.index.isin(df.sample(frac=0.05, random_state=1).index)  # 5% check
    df.to_csv(output_path, index=False)
    print("---------------")
    print(f"Finished QC - CSV report saved to {output_path}")
    print("---------------")
    print(f"Checking QC report")
    print(f"{len(df)} files QC")
    print(df.tile.value_counts())
    print("---------------")

    # Run df checks
    check_crs(df)
    check_dtype(df)
    check_within_range(df)
    check_valid_cog(df)
    check_nodata(df)
    check_extent_match(df)
    check_aligned(df)
    check_resolution(df)
    check_units(df)

    logger.info("Checking QC report complete")


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        "-d",
        nargs=2,
        metavar=("start", "end"),  # Describes each argument
        help="Search for files between start and end dates, e.g. 2021-01-01 2021-01-31",
    )
    parser.add_argument(
        "--inputdir",
        "-i",
        default="/gws/nopw/j04/defra_eo/public/change-detection/indices/sentinel_2/",
        help="The base input directory where indices files are stored",
    )
    parser.add_argument(
        "--outputdir",
        "-o",
        default="/gws/nopw/j04/defra_eo/data/output/change-detection/qc",
        help="The output directory in which to save the CSV output",
    )
    parser.add_argument(
        "--arddir",
        "-a",
        default="/neodc/sentinel_ard/data/sentinel_2",
        help="The root ard directory in used to test again ard files",
    )
    args = parser.parse_args()
    run(args.date[0], args.date[1], args.inputdir, args.outputdir, args.arddir)
