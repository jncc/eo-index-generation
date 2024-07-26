import luigi

import workflow.common.Defaults as defaults
from workflow.processing.ValidateIndices import ValidateIndicesForS1
from workflow.processing.ValidateIndices import ValidateIndicesForS2

from luigi import LocalTarget
from luigi.parameter import EnumListParameter


class FinaliseS1Workflow(luigi.WrapperTask):
    productId = luigi.Parameter()
    indices = EnumListParameter(
        enum=defaults.S1Indices,
        description="A comma separated list of any of RVI,VVVH,VHVV,RFDI",
        default=defaults.S1IndexDefaults["defaultIndices"])

    def requires(self):
        for index in self.indices:
            yield ValidateIndicesForS1(productId=self.productId, indices=[index], parallel=index.value)


class FinaliseS2Workflow(luigi.WrapperTask):
    productId = luigi.Parameter()
    indices = EnumListParameter(
        enum=defaults.S2Indices,
        description="A comma separted list of any of Brightness,EVI,GLI,GNDVI,GRVI,NBR,NDMI,NDVI,NDWI,RB,RDVI,RG,SAVI,SBL",
        default=defaults.S2IndexDefaults["defaultIndices"])

    def requires(self):
        for index in self.indices:
            yield ValidateIndicesForS2(productId=self.productId, indices=[index], parallel=index.value)
