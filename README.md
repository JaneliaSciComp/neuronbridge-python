# neuronbridge-python
Python API for NeuronBridge


## Development Notes

### Useful shell commands

To update conda_requirements.txt:

    conda env export --from-history --file conda_requirements.txt

To update requirements.txt:

    pipreqs --savepath=requirements.txt && pip-compile

### Publishing a new release

1) Update the version in setup.py
2) Push all changes and tag a release in GitHub
3) Build PyPI distribution:
    
    python setup.py sdist bdist_wheel

4) Upload to PyPI:

    twine upload dist/*


