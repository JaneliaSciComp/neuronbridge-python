# NeuronBridge Python API

[![DOI](https://zenodo.org/badge/479832149.svg)](https://zenodo.org/badge/latestdoi/479832149)

A Python API for the [NeuronBridge](https://github.com/JaneliaSciComp/neuronbridge) neuron similarity search service.

See [this notebook](notebooks/python_api_examples.ipynb) for usage examples.

![Data Model Diagram](model_diagram.png)


## Development Notes

Create a conda env with all the dependencies including Jupyter:

    conda env create -f environment.yml
    conda activate neuronbridge-python

Then install it as a Jupyter kernel:

    python -m ipykernel install --user --name=neuronbridge-python


### Install for development

You can install the module for development like this:

    pip install -e .


### Useful shell commands

To update requirements-universal.txt for UV:

    uv pip compile requirements.txt --universal --output-file  requirements-universal.txt

To update conda_requirements.txt:

    conda env export --from-history --file conda_requirements.txt

Regenerate the JSON schemas:

    python neuronbridge/generate_schemas.py

Run the unit tests:

    pytest tests

Migrate to UV:

    uv pip compile requirements.txt --universal --output-file  requirements-universal.txt
    uv venv
    uv pip sync requirements-universal.txt
    uv pip install -e .


### Publishing a new release

1) Update the version in setup.py
2) Push all changes and tag a release in GitHub
3) Build PyPI distribution:

    python setup.py sdist bdist_wheel

4) Upload to PyPI:

    twine upload dist/*


### Running validation using Ray

You can run validation multithreaded on a single machine like this:

    ./neuronbridge/validate_ray.py --dashboard --cores 60

To run the validation script in a distributed manner on the Janelia cluster, you must first install [ray-janelia](https://github.com/JaneliaSciComp/ray-janelia) in a sister directory to where this code base is cloned. Then run a script to bsub the Ray cluster:

    ./scripts/launch_validation.sh
