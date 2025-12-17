import os
import sys

# add project root to sys.path so Sphinx can import 'exercices' package
sys.path.insert(0, os.path.abspath(".."))  # if conf.py is in docs/, this points to project root

# extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
]

# theme
html_theme = "sphinx_rtd_theme"
