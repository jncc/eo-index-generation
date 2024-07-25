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
