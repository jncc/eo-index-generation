import luigi
import os
import re
import json
import workflow.common.Defaults as defaults
import logging

from luigi.util import requires
from luigi import LocalTarget

from workflow.processing.PrepareProcessing import PrepareProcessing
from workflow.processing.GenerateS2Index import GenerateS2Index

log = logging.getLogger('luigi-interface')


@requires(PrepareProcessing)
class GenerateS2Indices(luigi.Task):
    productId = luigi.Parameter()
    indices = luigi.parameter.EnumListParameter(
        enum=defaults.S2Indices,
        description="A comma separted list of any of Brightness,EVI,GLI,GNDVI,GRVI,NBR,NDMI,NDVI,NDWI,RB,RDVI,RG,SAVI,SBL",
        default=defaults.S2IndexDefaults["defaultIndices"])

    def run(self):
        with self.input().open('r') as pp:
            ardFiles = (json.load(pp))["ardFiles"][0]

        indexGenerationTasks = []
        for index in self.indices:
            indexGenerationTasks.append(
                GenerateS2Index(
                    productId=self.productId,
                    index=[index],
                    ardFiles=ardFiles,
                    _stateFileName=f"GenerateS2Index_{index.value}.json"
                )
            )

        yield indexGenerationTasks

        indicesProducts = []
        for task in indexGenerationTasks:
            with task.output().open('r') as o:
                indicesProducts.append(json.load(o)["indicesFiles"])

        output = {
            "indicesFiles": indicesProducts
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, 'GenerateS2Indices.json')
        return LocalTarget(outFile)
