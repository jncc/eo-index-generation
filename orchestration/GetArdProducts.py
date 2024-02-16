import luigi
import json
import os
from luigi.util import requires
from ceda_ard_finder import CreateSymlinks

## probably need to call CreateSymLinks directly from run to specify correct output path.
@requires(CreateSymlinks)
class GetArdProducts(luigi.Task):
    stateLocation = luigi.Parameter()
    
    def run(self):

        with self.output().open("w") as outFile:
            output = {
                "message": "done a thing"
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))


    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, "GetArdProducts.json"))