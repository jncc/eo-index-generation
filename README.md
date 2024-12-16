# EO Indices Generation

Orchestrates and submits jobs to the JASMIN LOTUS cluster which generate (unmasked) indices for S1 and S2 ARD products.

## Pre-requisites

* Access to the CEDA Archive
* The CEDA ARD Finder Repository - <https://github.com/jncc/ceda_ard_finder>
* A JASMIN account with access to the LOTUS cluster ...
* ... OR a local machine with multiple CPU cores and sufficient RAM to run the index generation jobs.

## Supported Indices

The following indices have been tested and are supported:

* **S1**: `VHVV`
* **S2**: `NBR`, `NDMI`, `NDVI`, `NDWI`, `EVI2`

## Local Development

### The Workflow Container

Build the Docker container:

```bash
cd container
docker build --no-cache --target workflow -t eo-index-container .
```

Convert to Apptainer image:

```bash
apptainer build --force eo-index-container.sif docker-daemon://eo-index-container:latest
```

### Testing

The entire process (Orchestration + Workflow) cannot be tested locally due to the need to mount the CEDA Archive and submit jobs to LOTUS. However, individual components can be tested.

Example command to orchestrate the processing of S2 indices `NBR` and `NDMI` for products between `2022-06-06` and `2022-06-07`:

(Note: Install dependencies first `pip install -r requirements.txt` and change paths accordingly)

```bash
PYTHONPATH=. luigi --module orchestration SubmitJobsForS2 \
  --workingFolder /workingFolder \
  --stateFolder /stateFolder \
  --templatesDir /eo-index-generation/orchestration/templates \
  --basketFolder /ignore/this/basketFolder \
  --outputFolder /ignore/this \
  --containerPath /ignore/this \
  --indices NBR,NDMI \
  --startDate 2022-06-06 \
  --endDate 2022-06-07 \
  --ardFilter '*' \
  --satelliteFilter 'Sentinel-2A ARD, Sentinel-2B ARD' \
  --spatialOperator intersects \
  --testProcessing \
  --local-scheduler

```

Example command to process S2 indices `NBR` and `NDMI` for a single product:

(Note: Make sure to fill in the correct bind mounts, and have all the ARD products downloaded and available in the input folder)

```bash
apptainer exec \
  --bind :/input \
  --bind :/output \
  --bind :/state \
  --bind :/working \
  --bind :/tmp \
  eo-index-container.sif /app/exec.sh \
    --module workflow.processing ValidateIndicesForS2 \
    --productId S2B_20220606_lat50lon363_T30UVA_ORB080_utm30n_osgb \
    --indices NBR,NDMI \
    --workers 2 \
    --local-scheduler
```
