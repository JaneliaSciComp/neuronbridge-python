from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    requirements = [l for l in requirements if not l.strip().startswith('#')]

setup(
    name='neuronbridge-python',
    packages=find_packages(),
    version='1.0.0',
    description='Python API for NeuronBridge',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Konrad Rokicki',
    author_email='rokickik@janelia.hhmi.org',
    url='https://github.com/JaneliaSciComp/neuronbridge-python/',
    license='BSD 3-Clause',
    install_requires=requirements,
    setup_requires=['pytest-runner'],
    tests_require=['pytest==6.2.5'],
    test_suite='tests',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ], 
    python_requires='>=3.8',
)
