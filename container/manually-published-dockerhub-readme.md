# EO JASMIN Indices Container

## What is this?

This container supports the generation of **unmasked** indices for Sentinel-1 and Sentinel-2 Analysis Ready Data (ARD) products, specifically made to be run on a JASMIN LOTUS cluster

The `dockerfile` along with the codebase can be found on [GitHub](https://github.com/jncc/eo-index-generation/blob/main/container/dockerfile)

## Usage

It is recommended to convert the Docker container to an [Apptainer](https://apptainer.org/docs/user/latest/quick_start.html#installation) image for use on JASMIN and other machines that may not have sudo privileges.

```bash
apptainer build eo-jasmin-indices-container-X.X.X.sif docker://jncc/eo-jasmin-indices-container:X.X.X
```

After downloading the container, it may now be used either locally, or on JASMIN by following the [README](https://github.com/jncc/eo-index-generation/blob/main/README.md) in the above GitHub repository.

### Additional Information

Build information is stored at `/app/build-info.json`

```bash
apptainer exec eo-jasmin-indices-container-1.0.3.sif cat /app/build-info.json
```

```json
{
  "Build": {
    "Version": "3",
    "Date": "Mon Sep 23 16:19:10 BST 2024",
    "Image": "aws/codebuild/standard:7.0",
    "ToolVersions": {
      "Docker": "Docker version 26.1.4, build 5650f9b",
      "Apptainer": "apptainer version 1.3.2"
    }
  },
  "Container": "eo-jasmin-indices-container-1.0.3.sif",
  "Environment": "live",
  "GitHub": {
    "Repo": "jncc/eo-index-generation",
    "Branch": "main",
    "Commit": "56eeb6bb00f595f089dc4a841465c93cb160e4db"
  }
}
```

**i.e.** The exact state of the `jncc/eo-index-generation` GitHub repository at the time of the container build is <https://github.com/jncc/eo-index-generation/tree/56eeb6bb00f595f089dc4a841465c93cb160e4db>
