# Configuration file for the Sphinx documentation builder.
project = 'Agentic Web Workstation'
copyright = '2026, MaxMasAI (Owner: Sahilkumardhala)'
author = 'MaxMasAI (Owner: Sahil Kumar Dhala - https://github.com/Sahilkumardhala)'
release = '2.5.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
