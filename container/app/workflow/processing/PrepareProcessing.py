import luigi
import os
import shutil
import json

import workflow.common.Defaults as defaults

from luigi import LocalTarget
from functional import seq


class PrepareProcessing(luigi.Task):
    # like "S2B_20200604_lat52lon234_T31UDT_ORB051_utm31n_osgb"
    # or   "S1B_20200703_52_desc_063001_063026_VVVH_G0_GB_OSGB_RTCK_SpkRL"
    productId = luigi.Parameter()
    workingFolder = luigi.Parameter(default=defaults.Paths["working"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    inputFolder = luigi.Parameter(default=defaults.Paths["input"])

    def copyFileToWorking(self, fileName, workingPath):
        source = os.path.join(self.inputFolder, fileName)
        target = os.path.join(workingPath, fileName)

        shutil.copyfile(source, target)

        return target

    def run(self):
        if self.productId.find(".") > -1:
            raise Exception("Do not include the extension in the productId")

        # Copy files matching product id to working
        ardFiles = seq(os.listdir(self.inputFolder)) \
            .filter(lambda x: x.startswith(self.productId)) \
            .map(lambda x: self.copyFileToWorking(x, self.workingFolder)) \
            .to_list()

        if len(ardFiles) == 0:
            raise Exception(f"No ard files matching {self.productId}")

        output = {
            "ardFiles": ardFiles
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, 'PrepareProcessing.json')
        return LocalTarget(outFile)
