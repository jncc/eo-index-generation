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

from luigi import LocalTarget

log = logging.getLogger('luigi-interface')


class ValidateIndex(luigi.Task):
    productId = luigi.Parameter()
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])

    index = luigi.Parameter()  # i.e. NDMI
    indexFileName = luigi.Parameter()  # i.e. S2A_20220624_lat57lon375_T30VVJ_ORB123_utm30n_osgb_NDMI.tif
    indexFilePath = luigi.Parameter()  # i.e. /output/sentinel_2/ndmi/2022/06/24/S2A_20220624_lat57lon375_T30VVJ_ORB123_utm30n_osgb_NDMI.tif
    indexQcRange = luigi.ListParameter()
    ardFile = luigi.Parameter()  # i.e. /neodc/sentinel_ard/data/sentinel_2/2022/06/24/S2A_20220624_lat57lon375_T30VVJ_ORB123_utm30n_osgb_sat.tif

    _stateFileName = luigi.Parameter()  # i.e. ValidateIndexForS2_NDMI.json

    def get_size(self):
        size = os.path.getsize(self.indexFilePath)
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024 ** 2:
            return f"{round(size/1024, 2)} KB"
        elif size < 1024 ** 3:
            return f"{round(size/(1024 ** 2), 2)} MB"
        elif size < 1024 ** 4:
            return f"{round(size/(1024 ** 3), 2)} GB"

    def get_stats(self):
        # determine if the file is a valid cog
        valid_cog, _, _ = rio_cogeo.cog_validate(self.indexFilePath)

        with rasterio.open(self.indexFilePath) as dataset:
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
            meta["path"] = self.indexFilePath
            meta["filesize"] = self.get_size()
            meta["index"] = self.index
            meta["overview"] = bool(dataset.overviews(1))
            meta["is_resolution_10"] = bool(pixel == (10.0, 10.0))
            meta["is_units_m"] = bool(units == "metre")
            meta["QC_date"] = date.today()
            meta["ARD_date"] = datetime.strptime(re.search(r".*_(\d{4}\d{2}\d{2})_.*", self.indexFileName).group(1), "%Y%m%d").date()
            meta["tile"] = re.sub(fr"_{self.index}.tif$", "", self.indexFileName, flags=re.IGNORECASE)

            meta["within_range"] = bool(meta["min"] > self.indexQcRange[0] and meta["max"] < self.indexQcRange[1])

            meta["valid_cog"] = valid_cog

            with rasterio.open(self.ardFile) as arddataset:
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

    def run(self):
        output = {
            "productId": self.productId,
            "qcResults": self.get_stats()
        }
        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)
