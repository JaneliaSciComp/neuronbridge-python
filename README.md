# neuronbridge-python

A Python API for the [NeuronBridge](https://github.com/JaneliaSciComp/neuronbridge) neuron similarity search service. 

See [this notebook](notebooks/python_api_examples.ipynb) for usage examples.

## Development Notes

### Useful shell commands

To update conda_requirements.txt:

    conda env export --from-history --file conda_requirements.txt

To update requirements.txt:

    pipreqs --savepath=requirements.txt && pip-compile

Regenerate the JSON schemas:

    python neuronbridge/generate_schemas.py

Run the unit tests:

    pytest tests


### Publishing a new release

1) Update the version in setup.py
2) Push all changes and tag a release in GitHub
3) Build PyPI distribution:
    
    python setup.py sdist bdist_wheel

4) Upload to PyPI:

    twine upload dist/*


