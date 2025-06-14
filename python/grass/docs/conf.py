# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import string
import sys

# -- Additional Paths -- -----------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
if not os.getenv("GISBASE"):
    import logging

    logging.fatal("GISBASE not defined")
    sys.exit("GISBASE not defined")
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.environ["GISBASE"], "etc", "python", "grass")),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "ctypes")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "exceptions")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "gunittest")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "imaging")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "pydispatch")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "pygrass")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "script")
    ),
)
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.environ["GISBASE"], "etc", "python", "grass", "temporal")
    ),
)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "GRASS Python Library"
copyright = "2025, GRASS Development Team"
author = "GRASS Development Team"
release = "8.5.0dev"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.ifconfig",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True
