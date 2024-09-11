import luigi
import json
import os
import re
import logging
from ceda_ard_finder import CreateSymlinks

log = logging.getLogger('luigi-interface')


class GetArdProducts(luigi.Task):
    stateFolder = luigi.Parameter()
    basketFolder = luigi.Parameter()

    # Ceda Ard Finder Params
    startDate = luigi.DateParameter()
    endDate = luigi.DateParameter()
    ardFilter = luigi.Parameter()
    spatialOperator = luigi.ChoiceParameter(choices=["", "intersects", "disjoint", "contains", "within"])
    satelliteFilter = luigi.Parameter()

    # Optional, rarely used Params
    orbit = luigi.IntParameter(default=-9999)
    orbitDirection = luigi.Parameter(default="")
    wkt = luigi.Parameter(default="")

    @staticmethod
    def parse_product(product):
        parsedProduct = ""
        if product.startswith("S1"):
            parsedProduct = re.sub(r"\.tif$", "", product)
        elif product.startswith("S2"):
            parsedProduct = re.sub(r"_vmsk_sharp_rad_srefdem_stdsref\.tif$", "", product)
        return parsedProduct

    def run(self):
        task = CreateSymlinks(
            stateFolder=self.stateFolder,
            productLocation=self.basketFolder,
            startDate=self.startDate,
            endDate=self.endDate,
            ardFilter=self.ardFilter,
            spatialOperator=self.spatialOperator,
            satelliteFilter=self.satelliteFilter,
            orbit=self.orbit,
            orbitDirection=self.orbitDirection,
            wkt=self.wkt,
        )
        result = yield task

        products = []
        with result.open("r") as createSymlinksFile:
            products = [self.parse_product(os.path.basename(product)) for product in json.load(createSymlinksFile)["products"]]

        with self.output().open("w") as outFile:
            output = {
                "products": products
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateFolder, "GetArdProducts.json"))
