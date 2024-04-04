# EEG-ExPy Documentation Developer Notes

The documentation page can be found at https://neurotechx.github.io/eeg-expy

The documentation source files are a combination of plain-text `.rst`, `.md`, and `.py` files. 

It is built locally with `sphinx`, and hosted on the github repo `gh-pages` branch in the usual fashion


There are two main locations for the documentation files:

- The various files and sub-folders in  `eeg-expy/doc`, which contain the webpage contents
- The files and sub-folders in `eeg-expy/examples`, which contains `.py` scripts, grouped by experiment

This general organization (with `doc` and `examples` folders) is widely used by excellent python libraries such as `MNE` and `Nilearn`, and we are largely following suit in the organization here. 

The `.py` files in `examples` contain mixtures of python code and `.rst`-format documentation, which are converted through `sphinx-gallery` into a set of web-pages with formatted text and code and in-line figures. In addition, `sphinx-gallery` creates executable `.py` and `.ipynb` files for each example page, and adds download links to these at the bottom of each page. 

The documentation building command actually executes the python code in each of the `examples` files, and creates figures from them. Errors in the python code lead to incompletely built webpages. 


( Side-note: The title `EEG-Notebooks` was originally conceived with the idea of having complete Python-based EEG experiments runnable from a jupyter notebook, with those notebooks being the main contents of the repo. At the user-level, this is still largely the case; but at the development level, we have now switched over from maintaining a set of `ipynb` source files, to maintaining a set of `.py` files (in the `examples folder), that are converted to `.ipynb` files when the `sphinx-gallery` documentation is compiled. This is much better and sustainable from the point of view of version control, since multiple-user contributions to `ipynb` files gets very hairy with git )


## Building the doc site

The documentation build has only been tested in linux. It may also work on Mac. 

First: install the docs dependencies in a new or existing python environment
(see `requirements-doc.txt`)

When working on the docs, it is most useful to have 3 terminals open, each with the python environment activated. 

In terminal 1: edit the source files

In terminal 2: build and re-build the docs periodically to inspect changes

`cd eeg-expy/doc`
`make html`

In terminal 3: keep a local http server running to render the docs

`python -m http.server 8001`


In browser, navigate to the port used above

`localhost:8001`


When you are happy with the changes, commit and push the source files, and run the command that builds documentation and pushes to `gh-pages` 

`make install`




## Misc notes

- The `doc/index.rst` defines the overall site structure and table-of-contents tree
- `doc/Makefile` contains the commands for building documentation. The main two commands are `make html` (build docs locally) and `make install` (build docs locally and push to `gh-pages` branch, updating the website`)
- Examples pages can be built individually, rather than re-running the entire doc build process
- The current doc build takes approximately 10 minutes
 


