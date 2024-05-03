#!/bin/bash
rm -rf dist
python -m pip install --upgrade build
python -m build
python -m pip install --user --upgrade twine
python -m twine upload dist/*
