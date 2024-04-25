# OAPapersViewer
TUI viewer for OAPapers corpus and derived datasets.

You can find the home repository of the OAPapers project at [https://github.com/KNOT-FIT-BUT/OAPapers](https://github.com/KNOT-FIT-BUT/OAPapers)

![TUI Viewer](tui_viewer.png)

## Install

    pip install oapapersviewer

## Usage

An example of loading OARelatedWork dataset with references:

```python
oapapersviewer train.jsonl -r references.jsonl -rw
```

