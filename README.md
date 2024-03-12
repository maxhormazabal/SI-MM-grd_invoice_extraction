# example_package

## Index

1. [Overview](#overview)
2. [Requirements](#requirements)
2. [Pre-commit Hooks](#hooks)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Tests](#tests)
6. [Run](#run)
7. [Project Organization](#folders)

## <a name="overview">Overview</a>

example project to be used as a template

## <a name="requirements">Requirements</a>

This project has been developed using [Setuptools](https://setuptools.readthedocs.io/en/latest/).
So, `Python 3` and `pip3` are required.

## <a name="hooks">Pre-commit hooks</a>

This project uses pre-commit hooks to check code quality and format before it s finally committed to the repository. To
configure the pre-commit hooks to evaluate your code, follow this steps:

1. Install pre-commit utility: `pip install pre-commit`
2. Run inside the root directory the following command: `pre-commit install`
3. Done

After this setup, black and flake should run before each commit command

```
git commit -m "example commit"
[INFO] Installing environment for https://github.com/psf/black.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
black....................................................................Passed
flake8...................................................................Passed
[master 12a838b] example commit
```

If you don't follow the style guide, this tools will show warning and they will abort your commit

```
git commit -m "example commit"
black....................................................................Failed
- hook id: black
- files were modified by this hook

reformatted example_package/common/infraestructure/timescale_engine.py

All done! ✨ 🍰 ✨
1 file reformatted, 3 files left unchanged.

flake8...................................................................Failed
- hook id: flake8
- exit code: 1

example_package/cli.py:12:80: E501 line too long (88 > 79 characters)
example_package/common/infraestructure/timescale_engine.py:10:80: E501 line too long (88 > 79 characters)

```

## <a name="installation">Installation</a>

All the other required python packages may be installed using the command:

```bash
pip3 install -e .

# or may be required

pip3 install -e --user . 
```

A new requirement must be added to the `install_requires` property within the `setup.py` file.

## <a name="configuration">Configuration</a>

All the configuration variables are included on **.env** files. For
further information read the [related documentation](https://pypi.org/project/python-dotenv/). An example **.env** file
is provided `.env.example` you can use it as a base **.env** file if you rename it to `.env`

## <a name="tests">Tests</a>

```bash
# All tests
pytest

# All tests verbose mode (not encouraged use logging module instead)
pytest -s --log-cli-level=INFO

# Unit tests
pytest -s --log-cli-level=INFO example_package/tests/unit

# Integration tests
pytest -s --log-cli-level=INFO example_package/tests/integration

# Validation tests
pytest -s --log-cli-level=INFO example_package/tests/validation
```

## <a name="run">Run (dev)</a>

### Place the models in extractor/models
They must be placed in
```
extractor/models/single
extractor/models/multi
```

### Run the OCR
To run the system you must have the OCR launched locally (last version in harbor.gradiant.org).

```bash
docker run -p 8080:80 <ocr-tag>
```

 And then run the system indicating a directory with orders to be processed:

```bash
python3 extractor/main.py --directoryPath
    path_to_dir/valida_info_extractor/procesar
    --resultsPath
    path_to_dir/valida_info_extractor/output/
    --class_output_path
    path_to_dir/valida_info_extractor/class_output/
```

## <a name="folders"> Project Organization</a>

This template project contains a python module *example_package*:

```
example_package
├── cli.py
├── common
│   ├── configuration
│   │   ├── config.py
│   │   └── __init__.py
│   ├── infraestructure
│   │   ├── abstract_engine.py
│   │   ├── __init__.py
│   │   └── timescale_engine.py
│   ├── __init__.py
│   └── usecases
│       ├── base.py
│       └── __init__.py
├── example_domain
│   ├── __init__.py
│   ├── services
│   │   └── __init__.py
│   └── usecases
│       ├── __init__.py
│       └── test_connection.py
├── __init__.py
└── tests
    ├── __init__.py
    ├── integration
    │   └── __init__.py
    ├── system
    │   └── __init__.py
    ├── unit
    │   ├── __init__.py
    │   └── test_example.py
    └── utils.py
```

* *cli.py*: contains the commands that can be launched from command line
* *common* folder*: common definitions and fucntions shared among the different domains
* *example_domain*: an example of a sub-module that implements a functionality that can be instantiated by the cli
    * *services*: contains the functions used in the domain. Every function that needs to be implemente should be a
      service. Services must have comprehensive names.
    * *usecases*: a usecase should be a sequence of service calls. Usecases must be understandable without prior
      knowledge of the code.
* *tests* contains the tests of the module


## Consideraciones

0. Pasos iniciales
    - Descargar modelos https://repo.gradiant.org/nexus/repository/raw-dataset-si/model/0.8.3/megasa_onnx_0_8_3.tar.gz
    - Mover carpeta models dentro de extractor
    - Crear una carpeta logs
    
1. Crear el entorno

```
conda create --name facturas_grd python=3.9
```

2. Instalar librerías

```
pip3 install -e .
```

3. Ejecutar
```
python3 -m extractor.main --directoryPath valida_info_extractor/procesar --resultsPath valida_info_extractor/output/ --class_output_path valida_info_extractor/class_output/
```