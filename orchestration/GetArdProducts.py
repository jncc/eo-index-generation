import luigi
import json
import os
from luigi.util import requires
from ceda_ard_finder import CreateSymlinks


@requires(CreateSymlinks)
class GetArdProducts(luigi.Task):
    stateLocation = luigi.Parameter()

    def run(self):
        products = []
        with self.input().open("r") as createSymlinksFile:
            products = json.load(createSymlinksFile)["products"]

        with self.output().open("w") as outFile:
            output = {
                "products": products
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, "GetArdProducts.json"))
