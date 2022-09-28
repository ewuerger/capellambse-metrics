..
   SPDX-FileCopyrightText: Copyright capellambse-metrics contributors
   SPDX-License-Identifier: Apache-2.0

capellambse_metrics
===================

.. image:: https://github.com/ewuerger/capellambse-metrics/actions/workflows/build-test-publish.yml/badge.svg
  :target: https://github.com/ewuerger/capellambse-metrics/actions/workflows/build-test-publish.yml/badge.svg

.. image:: https://github.com/ewuerger/capellambse-metrics/actions/workflows/lint.yml/badge.svg
  :target: https://github.com/ewuerger/capellambse-metrics/actions/workflows/lint.yml/badge.svg

A streamlit dashboard for visualizing metrics of capellambse models.

Running
-------

Configure which Capella model is to be taken as the basis for your dashboard
with the `config.yaml` file:

.. code::

    # SPDX-FileCopyrightText: Copyright capellambse-metrics contributors
    # SPDX-License-Identifier: Apache-2.0

    model:
        path: PATH_TO_MODEL # for e.g. git+https|ssh://...
        entrypoint: PATH_TO_AIRD
        revision: nightly # Optional: Defaults to HEAD in capellambse

    earlier_model_revision: BL0-Release # Optional for deltas in metrics
    # branch names and tags are allowed here

Then make sure to cd into the `capellambse_metrics` folder before executing
the following command:

.. code::

    streamlit run app.py

The dashboard should then be served on localhost:8501.

Documentation
-------------

Read the `full documentation on Github pages`__.

__ https://ewuerger.github.io/capellambse-metrics

Installation
------------

You can install the latest released version directly from PyPI.

.. code::

    pip install capellambse-metrics

To set up a development environment, clone the project and install it into a
virtual environment.

.. code::

    git clone https://github.com/ewuerger/capellambse-metrics
    cd capellambse-metrics
    python -m venv .venv

    source .venv/bin/activate.sh  # for Linux / Mac
    .venv\Scripts\activate  # for Windows

    pip install -U pip pre-commit
    pip install -e '.[docs,test]'
    pre-commit install

Contributing
------------

We'd love to see your bug reports and improvement suggestions! Please take a
look at our `guidelines for contributors <CONTRIBUTING.rst>`__ for details.

Licenses
--------

This project is compliant with the `REUSE Specification Version 3.0`__.

__ https://git.fsfe.org/reuse/docs/src/commit/d173a27231a36e1a2a3af07421f5e557ae0fec46/spec.md

Copyright DB Netz AG, licensed under Apache 2.0 (see full text in `<LICENSES/Apache-2.0.txt>`__)

Dot-files are licensed under CC0-1.0 (see full text in `<LICENSES/CC0-1.0.txt>`__)
