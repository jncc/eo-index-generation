import luigi
import os
import json
import workflow.common.Defaults as defaults
import logging
import rasterio
import numpy

from functional import seq
from luigi.util import requires
from luigi import LocalTarget
from workflow.processing.GenerateS1Indices import GenerateS1Indices
from workflow.processing.GenerateS2Indices import GenerateS2Indices

log = logging.getLogger('luigi-interface')

class EnforceArdRasterProperties(luigi.Task):
    outputFolder = luigi.Parameter(default=defaults.Paths["output"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    workingFolder = luigi.Parameter(default=defaults.Paths["working"])

    _stateFileName = ""

    def getArdRasterProperties(dataFile):
        with rasterio.open(dataFile) as data:
            crs = data.crs
            shape = data.shape
            transform = data.transform

        return crs, shape, transform
    
    def getIndexRasterProperties(dataFile):
        with rasterio.open(dataFile) as data:
            crs = data.crs
            transform = data.transform
            dtypes = data.dtypes
            data = data.read()

        return crs, transform, dtypes, data

    def run(self):
        with self.input().open('r') as pp:
            ardFiles = (json.load(pp))["ardFiles"]

        with self.input().open('r') as ix:
            indicesFiles = (json.load(ix))["indicesFiles"]

        correctedDir = os.path.join(self.workingFolder, "indices-corrected")

        ardDataFile = seq(ardFiles) \
            .filter(lambda x: x.lower().endswith("_RTCK_SpkRL.tif") 
                    or x.lower().endswith("vmsk_sharp_rad_srefdem_stdsref.tif")) \
            .first()

        ard_crs, ard_shape, ard_transform = self.getArdRasterProperties(ardDataFile)

        output = {
            "correctedIndicesFiles": []
        }

        for index in indicesFiles:
            indexFile = index["indexfile"]
            index_crs, index_transform, index_dtypes, index_data = self.getIndexRasterProperties(indexFile)
            dst_data = numpy.empty(ard_shape, dtype=index_dtypes[0])
            correctIndexFilePath = os.path.join(correctedDir, os.path.basename(indexFile))

            rasterio.warp.reproject(
                index_data,
                dst_data,
                src_transform=index_transform,
                src_crs=index_crs,
                dst_transform=ard_transform,
                dst_crs=ard_crs)
            
            with rasterio.open(
                correctIndexFilePath,
                'w',
                driver='GTiff',
                width=ard_shape[1],
                height=ard_shape[0],
                count=1,
                dtype=index_dtypes[0],
                nodata=-9999,
                transform=ard_transform,
                crs=ard_crs) as dst:
                dst.write(dst_data, indexes=1)

            output["correctedIndicesFiles"].append(correctIndexFilePath)

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)

@requires(GenerateS1Indices)
class EnforceS1ArdRasterProperties(EnforceArdRasterProperties):
    _stateFileName = "EnforceS1ArdRasterProperties.json"

    def nullFunction(self):
        pass

@requires(GenerateS2Indices)
class EnforceS2ArdRasterProperties(EnforceArdRasterProperties):
    _stateFileName = "EnforceS2ArdRasterProperties.json"

    def nullFunction(self):
        pass
