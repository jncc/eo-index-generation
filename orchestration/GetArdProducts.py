import luigi
import json
import os
import re
import logging
from luigi.util import inherits, common_params
from ceda_ard_finder import CreateSymlinks

log = logging.getLogger('luigi-interface')


@inherits(CreateSymlinks)
class GetArdProducts(luigi.Task):
    stateFolder = luigi.Parameter()
    basketFolder = luigi.Parameter()
    productLocation = ""  # Placeholder required for inheritance

    def requires(self):
        return CreateSymlinks(
            productLocation=self.basketFolder,  # The symlink location is different in the CEDA ARD Finder ...
            **common_params(self, CreateSymlinks)  # ... Everything else is the same
        )

    @staticmethod
    def parse_product(product):
        parsedProduct = ""
        if product.startswith("S1"):
            parsedProduct = re.sub(r"\.tif$", "", product)
        elif product.startswith("S2"):
            parsedProduct = re.sub(r"_vmsk_sharp_rad_srefdem_stdsref\.tif$", "", product)
        return parsedProduct

    def run(self):
        products = []
        with self.input().open("r") as createSymlinksFile:
            products = [self.parse_product(os.path.basename(product)) for product in json.load(createSymlinksFile)["products"]]

        with self.output().open("w") as outFile:
            output = {
                "products": products
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateFolder, "GetArdProducts.json"))
