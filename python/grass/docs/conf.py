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
from grass.script import core  # noqa: E402, C0413

footer_tmpl = string.Template(
    r"""
{% block footer %}<hr class="header">
<p><a href="../index.html">Help Index</a>
 | <a href="../topics.html">Topics Index</a>
 | <a href="../keywords.html">Keywords Index</a>
 | <a href="../full_index.html">Full Index</a></p>
<p>&copy; 2003-${year} <a href="https://grass.osgeo.org">
GRASS Development Team</a>, GRASS ${grass_version} Documentation</p>
{% endblock %}
"""
)

grass_version = core.version()["version"]

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "GRASS Python Library"
project_copyright = "%Y, GRASS Development Team"  # %Y is replaced by the year
author = "GRASS Development Team"
release = grass_version
version = grass_version  # Used for sitemap

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# If your documentation needs a minimal Sphinx version, state it here.
# 8.1: Copyright supports %Y placeholder
needs_sphinx = "8.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.ifconfig",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_sitemap",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
html_favicon = "_static/favicon.ico"

# The base URL which points to the root of the HTML documentation. It is used
# to indicate the location of document using the Canonical Link Relation.
html_baseurl = "https://grass.osgeo.org/grass-stable/manuals/libpython/"

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable/", None),
    "python": ("https://docs.python.org/3", None),
}

# -- Options for sphinx-sitemap extension ------------------------------------
# https://sphinx-sitemap.readthedocs.io/en/latest/advanced-configuration.html

sitemap_filename = "sitemap.xml"
# TODO: html_baseurl used here for sphinx_sitemap overwrites and contradicts with the
# variable html_baseurl set above for creating the canonical links
html_baseurl = "https://grass.osgeo.org/"
sitemap_url_scheme = "grass{version}manuals/libpython/{link}"
sitemap_excludes = [
    "search.html",
    "genindex.html",
]

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True
