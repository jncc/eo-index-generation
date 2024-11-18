import luigi
import json
import os
import re
import logging
from functional import seq
from datetime import datetime

from ceda_ard_finder import CreateSymlinksFromFilters, CreateSymlinksFromTextFileList

log = logging.getLogger('luigi-interface')


class GetArdProducts(luigi.Task):
    stateFolder = luigi.Parameter()
    basketFolder = luigi.Parameter()

    def run(self):

        result = yield self.task()

        products = []

        with result.open("r") as createSymlinksFile:
            products = seq(json.load(createSymlinksFile)["products"]) \
                .map(lambda x: os.path.basename(x)) \
                .map(lambda x: re.sub(r"\.tif$", "", x)) \
                .map(lambda x: re.sub(r"_vmsk_sharp_rad_srefdem_stdsref$", "", x)) \
                .to_list()

        if len(products) == 0:
            raise ValueError("No Products Found")

        with self.output().open("w") as outFile:
            output = {
                "products": products
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateFolder, "GetArdProducts.json"))


class GetArdProductsFromTextFileList(GetArdProducts):

    def task(self):
        return CreateSymlinksFromTextFileList(
            stateFolder=self.stateFolder,
            productLocation=self.basketFolder
        )


class GetArdProductsFromFilters(GetArdProducts):
    # Ceda Ard Finder Params
    startDate = luigi.Parameter()  # Date in YYYY-MM-DD format
    endDate = luigi.Parameter()
    ardFilter = luigi.Parameter()
    spatialOperator = luigi.ChoiceParameter(choices=["", "intersects", "disjoint", "contains", "within"])
    satelliteFilter = luigi.Parameter()

    # Optional, rarely used Params
    orbit = luigi.IntParameter(default=-9999)
    orbitDirection = luigi.Parameter(default="")
    wkt = luigi.Parameter(default="")

    def task(self):
        return CreateSymlinksFromFilters(
            stateFolder=self.stateFolder,
            productLocation=self.basketFolder,
            startDate=datetime.strptime(self.startDate, "%Y-%m-%d"),  # Format str to datetime object
            endDate=datetime.strptime(self.endDate, "%Y-%m-%d"),
            ardFilter=self.ardFilter,
            spatialOperator=self.spatialOperator,
            satelliteFilter=self.satelliteFilter,
            orbit=self.orbit,
            orbitDirection=self.orbitDirection,
            wkt=self.wkt
        )
