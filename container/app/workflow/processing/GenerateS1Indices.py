import luigi
import os
import json
import logging
import workflow.common.Defaults as defaults

from luigi.util import requires
from luigi.parameter import EnumListParameter
from luigi import LocalTarget

from workflow.processing.PrepareProcessing import PrepareProcessing
from workflow.processing.GenerateS1Index import GenerateS1Index

log = logging.getLogger('luigi-interface')


@requires(PrepareProcessing)
class GenerateS1Indices(luigi.Task):
    productId = luigi.Parameter()
    indices = EnumListParameter(
        enum=defaults.S1Indices,
        description="A comma separated list of any of RVI,VVVH,VHVV,RFDI",
        default=defaults.S1IndexDefaults["defaultIndices"])

    def run(self):
        with self.input().open('r') as pp:
            ardFiles = (json.load(pp))["ardFiles"]

        indexGenerationTasks = []
        for index in self.indices:
            indexGenerationTasks.append(
                GenerateS1Index(
                    productId=self.productId,
                    index=[index],
                    ardFiles=ardFiles,
                    _stateFileName=f"GenerateS1Index_{index.value}.json"
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
        outFile = os.path.join(self.stateFolder, 'GenerateS1Indices.json')
        return LocalTarget(outFile)
