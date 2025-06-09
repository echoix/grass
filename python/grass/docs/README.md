# GRASS Python Docs

## Local Development

### Prerequisites

Install the following dependencies from the `requirements.txt` file: in
`python/grass/docs` directory.

* [sphinx (>=v8.2.3)](https://www.sphinx-doc.org/en/master/changes/8.2.html)
* [sphinx-immaterial (>=v0.13.5)](https://sphinx-immaterial.readthedocs.io/en/stable/index.html)
* [sphinx-sitemap (>=v2.6.0)](https://sphinx-sitemap.readthedocs.io/en/latest/)

```bash
pip install -r python/grass/docs/requirements.txt
```

### Build the Documentation

To build the documentation, run the following command in the `python/grass/docs`
directory:

```bash
make sphinxdoclib
```

This will generate the documentation in the `dist` directory.

### View the Documentation

To view the documentation, open the `index.html` file in the
`dist/docs/html/libpython`
directory with a local web server.

## CI/CD

The documentation is built and deployed automatically using GitHub Actions.
The workflow is triggered on every push to the `main` branch `.github/workflows/documentation.yml`.
