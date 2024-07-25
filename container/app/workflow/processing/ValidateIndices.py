import luigi
import os
import json
import workflow.common.Defaults as defaults
import logging
import re
import math
from datetime import date, datetime
import rasterio
import rio_cogeo
import multiprocessing as mp
import pandas as pd

from luigi.util import requires
from luigi import LocalTarget
from workflow.processing.CopyIndicesCogsToOutput import CopyIndicesCogsToOutputForS1
from workflow.processing.CopyIndicesCogsToOutput import CopyIndicesCogsToOutputForS2

log = logging.getLogger('luigi-interface')


class ValidateIndices(luigi.Task):
    productId = luigi.Parameter()
    ardPath = luigi.Parameter()
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    outputFolder = luigi.Parameter(default=defaults.Paths["output"])

    _stateFileName = ""
    _satellite = ""
    _index_range = []

    @staticmethod
    def get_size(path):
        # https://stackoverflow.com/questions/6080477/how-to-get-the-size-of-tar-gz-in-mb-file-in-python
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024 ** 2:
            return f"{round(size/1024, 2)} KB"
        elif size < 1024 ** 3:
            return f"{round(size/(1024 ** 2), 2)} MB"
        elif size < 1024 ** 4:
            return f"{round(size/(1024 ** 3), 2)} GB"

    @staticmethod
    def get_stats(index_filepath, file_size, index, index_filename, ardFile, index_range):

        # determine if the file is a valid cog
        valid_cog, _, _ = rio_cogeo.cog_validate(index_filepath)

        with rasterio.open(index_filepath) as dataset:
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
            meta["path"] = index_filepath
            meta["filesize"] = file_size
            meta["index"] = index
            meta["overview"] = bool(dataset.overviews(1))
            meta["is_resolution_10"] = bool(pixel == (10.0, 10.0))
            meta["is_units_m"] = bool(units == "metre")
            meta["QC_date"] = date.today()
            meta["ARD_date"] = datetime.strptime(re.search(r".*_(\d{4}\d{2}\d{2})_.*", index_filename).group(1), "%Y%m%d").date()
            meta["tile"] = re.sub(fr"_{index}.tif$", "", index_filename, flags=re.IGNORECASE)

            meta["within_range"] = bool(meta["min"] > index_range[0] and meta["max"] < index_range[1])

            meta["valid_cog"] = valid_cog

            with rasterio.open(ardFile) as arddataset:
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

    @staticmethod
    def process(results):
        df = pd.DataFrame.from_dict(results)
        df["Check"] = df.index.isin(df.sample(frac=0.05, random_state=1).index)  # 5% check

        err = []

        len(df["crs"].unique()) == 1 or err.append("issue with CRS consistency")
        len(df["dtype"].unique()) == 1 or err.append("issue with data type consistency")
        len(df["within_range"].unique()) == 1 or err.append("issue with index range consistency")
        len(df["valid_cog"].unique()) == 1 or err.append("issue with one or more COGS")
        len(df["nodata"].unique()) == 1 or err.append("Inconsistent no data values")
        len(df["extent_match"].unique()) == 1 or err.append("Inconsistent extent")
        len(df["aligned"].unique()) == 1 or err.append("Inconsistent pixel alignement")
        len(df["is_resolution_10"].unique()) == 1 or err.append("Inconsistent resolution")
        len(df["is_units_m"].unique()) == 1 or err.append("Inconsistent units")

        if err:
            log.error(f"Issues with QC: {err}")

        res = {}
        dfc = df.copy()

        object_cols = dfc.select_dtypes(include=['object']).columns  # Convert objects to string so (hopefully) no error with json dump
        excluded_cols = ["ard_transform", "transform"]  # ... Exclude known good columns

        object_cols = [col for col in object_cols if col not in excluded_cols]
        dfc[object_cols] = dfc[object_cols].astype(str)

        dfc.set_index(["tile", "index"], inplace=True)
        dfc = dfc.T

        for (product, index) in dfc.columns:
            if product not in res:
                res[product] = {index: dfc[product, index].to_dict()}
            else:
                res[product].update({index: dfc[product, index].to_dict()})

        return res, err

    def _multi_run_wrapper(self, args):
        return self.get_stats(*args)

    def run(self):
        with self.input().open('r') as CopyIndicesCogsToOutput:
            cogFiles = (json.load(CopyIndicesCogsToOutput))["indicesCogFiles"]

        qc_data = []
        datestamp = re.findall("([0-9]{8})", self.productId)[0]

        if self._satellite == "S1":
            ardFile = f"{self.ardPath}/{datestamp[0:4]}/{datestamp[4:6]}/{datestamp[6:8]}/{self.productId}.tif"
        elif self._satellite == "S2":
            ardFile = f"{self.ardPath}/{datestamp[0:4]}/{datestamp[4:6]}/{datestamp[6:8]}/{self.productId}_sat.tif"

        for i in cogFiles:
            index = i["indexName"]  # i.e. NBR
            index_filename = os.path.basename(i["cogFilePath"])  # i.e. S2A_20220624_lat57lon375_T30VVJ_ORB123_utm30n_osgb_NDMI.tif
            index_filepath = i["cogFilePath"]  # i.e. /output/sentinel_2/ndmi/2022/06/24/S2A_20220624_lat57lon375_T30VVJ_ORB123_utm30n_osgb_NDMI.tif

            qc_data.append((
                index_filepath,
                self.get_size(index_filepath),
                index,
                index_filename,
                ardFile,
                self._index_range
            ))

        pool = mp.Pool(len(qc_data))
        results = pool.map(self._multi_run_wrapper, qc_data)
        processed_results = self.process(results)

        output = {
            "prodcutId": self.productId,
            "qcErrors": processed_results[1] if processed_results[1] else False,
            "qcResults": processed_results[0]
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    # def output(self):
    #     outFile = os.path.join(self.stateFolder, self._stateFileName)
    #     return LocalTarget(outFile)


@requires(CopyIndicesCogsToOutputForS1)
class ValidateIndicesForS1(ValidateIndices):
    parallel = luigi.Parameter(default=None)

    _satellite = "S1"
    _index_range = [-504, 504]

    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_1")

    def output(self):
        outFile = os.path.join(self.stateFolder, f"ValidateIndicesForS1{'_' + self.parallel if self.parallel else ''}.json")
        return LocalTarget(outFile)


@requires(CopyIndicesCogsToOutputForS2)
class ValidateIndicesForS2(ValidateIndices):
    _stateFileName = "ValidateIndicesForS2.json"
    _satellite = "S2"
    _index_range = [-1, 1]

    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_2")
