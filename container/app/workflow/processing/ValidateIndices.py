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
    def get_stats(index_filepath, file_size, index, index_filename, ardFile):

        # determine if the file is a valid cog
        valid_cog, _, _ = rio_cogeo.cog_validate(index_filepath)

        with rasterio.open(index_filepath) as dataset:
            meta = dataset.profile  # width, hight, crs etc
            indexBounds = dataset.bounds  # get boundary extent
            idt = dataset.transform  # get transformation params
            image = dataset.read()

            # Set all nodata values to 0
            image[image == meta["nodata"]] = 0

            meta["min"] = image.min()
            meta["max"] = image.max()
            meta["path"] = index_filepath
            meta["filesize"] = file_size
            meta["index"] = index
            meta["overview"] = bool(dataset.overviews(1))
            meta["QC_date"] = date.today()
            meta["ARD_date"] = datetime.strptime(re.search(r".*_(\d{4}\d{2}\d{2})_.*", index_filename).group(1), "%Y%m%d")
            meta["tile"] = re.sub(fr"_{index}.tif$", "", index_filename, flags=re.IGNORECASE)

            meta["within_range"] = "Y" if meta["min"] > -1 and meta["max"] < 1 else "N"

            meta["valid_cog"] = valid_cog

            with rasterio.open(ardFile) as arddataset:
                ardBounds = arddataset.bounds  # get boundary extent
                adt = arddataset.transform  # get transformation params

                if (math.isclose(ardBounds[0], indexBounds[0]) and
                    math.isclose(ardBounds[1], indexBounds[1]) and
                    math.isclose(ardBounds[2], indexBounds[2]) and
                        math.isclose(ardBounds[3], indexBounds[3])):

                    meta["extent_match"] = "Y"
                    meta["aligned"] = "Y" if math.isclose(idt[0], adt[0]) and math.isclose(idt[4], adt[4]) else "N"

                else:
                    meta["extent_match"] = "N"
                    meta["indexbounds"] = indexBounds
                    meta["ardbounds"] = ardBounds

            meta["ard_transform"] = adt
            meta["cell_size"] = f"{idt[0]}, {idt[4]}"  # writing cell size to file

            return meta

    @staticmethod
    def process(results, output_path):
        df = pd.DataFrame.from_dict(results)
        df["Check"] = df.index.isin(df.sample(frac=0.05, random_state=1).index)  # 5% check
        df.to_csv(output_path, index=False)

        len(df["crs"].unique()) == 1 or log.error("issue with CRS consistency, check QC file")
        len(df["dtype"].unique()) == 1 or log.error("issue with data type consistency, check QC file")
        len(df["within_range"].unique()) == 1 or log.error("issue with index range consistency, check QC file")
        len(df["valid_cog"].unique()) == 1 or log.error("issue with one or more COGS, check QC file")
        len(df["nodata"].unique()) == 1 or log.error("Inconsistent no data values, check QC file")
        len(df["extent_match"].unique()) == 1 or log.error("Inconsistent extent, check QC file")
        len(df["aligned"].unique()) == 1 or log.error("Inconsistent pixel alignement, check QC file")

    def _multi_run_wrapper(self, args):
        return self.get_stats(*args)

    def run(self):
        with self.input().open('r') as CopyIndicesCogsToOutput:
            cogFiles = (json.load(CopyIndicesCogsToOutput))["indicesCogFiles"]

        qc_data = []

        if self._satellite == "S1":
            pass
            # TODO: Implement this
        elif self._satellite == "S2":
            datestamp = re.findall("([0-9]{8})", self.productId)[0]
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
                ardFile
            ))

        pool = mp.Pool(len(qc_data))
        results = pool.map(self._multi_run_wrapper, qc_data)
        self.process(results, f"{self.outputFolder}/qc/{self.productId}_QC.csv")

        output = {
            "prodcutId": self.productId,
            "qcFile": f"{self.outputFolder}/qc/{self.productId}_QC.csv"
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)


@requires(CopyIndicesCogsToOutputForS1)
class ValidateIndicesForS1(ValidateIndices):
    _stateFileName = "ValidateIndicesForS1.json"
    _satellite = "S1"
    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_1")

    # TODO: Implement this

    def nullFunction(self):
        pass


@requires(CopyIndicesCogsToOutputForS2)
class ValidateIndicesForS2(ValidateIndices):
    _stateFileName = "ValidateIndicesForS2.json"
    _satellite = "S2"
    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_2")

    def nullFunction(self):
        pass
