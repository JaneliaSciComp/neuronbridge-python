# NeuronBridge Python API

[![DOI](https://zenodo.org/badge/479832149.svg)](https://zenodo.org/badge/latestdoi/479832149)

A Python API for the [NeuronBridge](https://github.com/JaneliaSciComp/neuronbridge) neuron similarity search service.

![Data Model Diagram](model_diagram.png)

## Installation

This library is available [on PyPI](https://pypi.org/project/neuronbridge-python/), so you can install it like this:

```bash
pip install neuronbridge-python
```

## Usage

The client will automatically select the latest version of the data and fetch it from S3. Here's a simple example of how to get an EM image by id:

```python
from neuronbridge import client
client = client.Client()
em_image = client.get_em_image(636798093) 
```

See [this notebook](https://github.com/JaneliaSciComp/neuronbridge-python/blob/main/notebooks/python_api_examples.ipynb) for complete usage examples.

## Development Notes

To build this code you will need to [install UV](https://docs.astral.sh/uv/getting-started/installation/).

Create a new UV virtual environment and install the dependencies:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip sync requirements-universal.txt
uv pip install -e .
```

### Running data validation using Ray

You can run validation multithreaded on a single machine like this:

```bash
./neuronbridge/validate_ray.py --dashboard --cores 60
```

To run the validation script in a distributed manner on the Janelia cluster, you must first install [ray-janelia](https://github.com/JaneliaSciComp/ray-janelia) in a sister directory to where this code base is cloned. Then run a script to bsub the Ray cluster:

```bash
./scripts/launch_validation.sh
```

### Updating requirements

After updating the requirements.txt file, you can sync the requirements-universal.txt file like this:

```bash
uv pip compile requirements.txt --universal --output-file  requirements-universal.txt
```

### Regenerate the JSON schemas:

```bash
python neuronbridge/generate_schemas.py
```

### Run the unit tests:

```bash
pixi run test
```

### Publishing a new release

1) Update the version in setup.py
2) Push all changes and tag a release in GitHub
3) Build PyPI distribution:

```bash
pixi run pypi-build
```

4) Upload to PyPI:

```bash
pixi run pypi-upload
```