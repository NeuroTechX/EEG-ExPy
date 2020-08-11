# -*- coding: utf-8 -*-

import sys
import os
import re

# If we are building locally, or the build on Read the Docs looks like a PR
# build, prefer to use the version of the theme in this repo, not the installed
# version of the theme.
def is_development_build():
    # PR builds have an interger version
    re_version = re.compile(r'^[\d]+$')
    if 'READTHEDOCS' in os.environ:
        version = os.environ.get('READTHEDOCS_VERSION', '')
        if re_version.match(version):
            return True
        return False
    return True

if is_development_build():
    sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath('./demo/'))

import sphinx_rtd_theme
from sphinx.locale import _


project = 'EEG Notebooks'
slug = re.sub(r'\W+', '-', project.lower())
version = '0.1.0'
release = '0.1.0'
author = u'John Griffiths, Jadin Tredup, NeuroTechX, & Contributors'
copyright = author
language = 'en'

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinxcontrib.httpdomain',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
source_suffix = ['.rst', '.md']
exclude_patterns = []
locale_dirs = ['locale/']
gettext_compact = False

master_doc = 'index'
suppress_warnings = ['image.nonlocal_uri']
pygments_style = 'default'

intersphinx_mapping = {
    'rtd': ('https://docs.readthedocs.io/en/latest/', None),
    'sphinx': ('http://www.sphinx-doc.org/en/stable/', None),
}

html_theme = 'sphinx_rtd_theme'
#html_theme_options = {
#    'logo_only': False,#True,
#    'navigation_depth': 5,
#}
html_context = {}

if not 'READTHEDOCS' in os.environ:
    html_static_path = ['_static/']
    html_js_files = ['debug.js']

    # Add fake versions for local QA of the menu
    html_context['test_versions'] = list(map(
        lambda x: str(x / 10),
        range(1, 100)
    ))

#html_logo = "demo/static/logo-wordmark-light.svg"
#html_logo = "img/eeg-notebooks_logo.png"
html_show_sourcelink = True

htmlhelp_basename = slug


latex_documents = [
  ('index', '{0}.tex'.format(slug), project, author, 'manual'),
]

man_pages = [
    ('index', slug, project, [author], 1)
]

texinfo_documents = [
  ('index', slug, project, author, slug, project, 'Miscellaneous'),
]


# Extensions to theme docs
def setup(app):
    from sphinx.domains.python import PyField
    from sphinx.util.docfields import Field

    app.add_object_type(
        'confval',
        'confval',
        objname='configuration value',
        indextemplate='pair: %s; configuration value',
        doc_field_types=[
            PyField(
                'type',
                label=_('Type'),
                has_arg=False,
                names=('type',),
                bodyrolename='class'
            ),
            Field(
                'default',
                label=_('Default'),
                has_arg=False,
                names=('default',),
            ),
        ]
    )

    
    # JG_ADD
    app.add_css_file('theme_override.css')





# ------------------------------------------------
# Sphinx gallery stuff

import os
from os.path import dirname as up
from datetime import date
import sphinx_gallery
#    import sphinx_bootstrap_theme
#import sphinx_rtd_theme
from sphinx_gallery.sorting import FileNameSortKey, ExplicitOrder

# Add any Sphinx extension module names here, as strings.
extensions += [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx_gallery.gen_gallery',
    'sphinx_copybutton',
    'numpydoc',
    'recommonmark', # JG_ADD
]

# Add any paths that contain templates here, relative to this directory.
#templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# numpydoc interacts with autosummary, that creates excessive warnings
# This line is a 'hack' for that interaction that stops the warnings
numpydoc_show_class_members = False

# Set to generate sphinx docs for class members (methods)
autodoc_default_options = {
    'members': None,
    'inherited-members': None,
}

# generate autosummary even if no references
autosummary_generate = True

# The suffix(es) of source filenames. Can be str or list of string
#source_suffix = '.rst' # ['.rst', '.md']
source_suffix = ['.rst', '.md']


# The master toctree document.
master_doc = 'index'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# Settings for sphinx_copybutton
copybutton_prompt_text = "$ "


html_theme_options = {
                      'canonical_url': '',
                      'analytics_id': 'UA-XXXXXXX-1',  #  Provided by Google in your dashboard
                      'logo_only': False,
                      'display_version': True,
                      'prev_next_buttons_location': 'bottom',
                      'style_external_links': False,
                      'vcs_pageview_mode': '',
                      'style_nav_header_background': 'white',
                      # Toc options
                      'collapse_navigation': False,#True,
                      'sticky_navigation': True,
                      'navigation_depth': 4,
                      'includehidden': True,
                      'titles_only': False
                                           }


"""
html_theme_options = {
    'navbar_sidebarrel': False,
    'navbar_links': [
        ("About", "about"),        
        ("Examples", "auto_examples/index"),
        ("User guide", "user_guide/index"),
        ("FAQ", "faq"),
        ("GitHub", "https://github.com/neurotechx/eeg-notebooks", True),
    ],

    # Set the page width to not be restricted to hardset value
    'body_max_width': None,

    # Bootswatch (http://bootswatch.com/) theme to apply.
    'bootswatch_theme': "flatly",

    # Render the current pages TOC in the navbar
    'navbar_pagenav': False,
}

# Settings for whether to copy over and show link rst source pages
html_copy_source = False
html_show_sourcelink = False
"""


# -- Extension configuration -------------------------------------------------


# Theme options to customize the look and feel, which are theme-specific.

# Settings for whether to copy over and show link rst source pages
html_copy_source = False
html_show_sourcelink = False


# -- Extension configuration -------------------------------------------------

# Configurations for sphinx gallery

sphinx_gallery_conf = {'filename_pattern': '(?=.*r__)(?=.*.py)', 
                       'examples_dirs': ['../examples','../examples/visual_n170', '../examples/visual_p300','../examples/visual_ssvep', '../examples/visual_cueing', '../examples/visual_gonogo'],
                       'gallery_dirs': ['auto_examples','auto_examples/visual_n170', 'auto_examples/visual_p300','auto_examples/visual_ssvep', 'auto_examples/visual_cueing', 'auto_examples/visual_gonogo'],
                       'within_subsection_order': FileNameSortKey,
                       'default_thumb_file': 'img/eeg-notebooks_logo.png',
                       'backreferences_dir': 'generated',   # Where to drop linking files between examples & API
                       'doc_module': ('eeg-notebooks'),
                       'reference_url': {'eeg-notebooks': None},
                       'remove_conffig_comments': True}

"""
sphinx_gallery_conf = {
        'filename_pattern': '.py', 
        'examples_dirs': ['../examples'],
        'gallery_dirs': ['auto_examples'],
        'subsection_order': ExplicitOrder([ '../examples/visual_n170',
                                            '../examples/visual_p300', 
                                            '../examples/visual_cueing',
                                            '../examples/visual_ssvep',
                                            '../examples/equipment_and_setup',
                                            '../examples/making_recordings',
                                            '../examples/stimulus_presentation',
                                            '../examples/analyzing_experimental_results',
                                            '../examples/complete_examples']),
    'within_subsection_order': FileNameSortKey,
    'default_thumb_file': 'img/eeg-notebooks_logo.png',
    'backreferences_dir': 'generated',   # Where to drop linking files between examples & API
    'doc_module': ('eeg-notebooks',),
    'reference_url': {'eeg-notebooksS': None},
    'remove_conffig_comments': True,
}

"""
