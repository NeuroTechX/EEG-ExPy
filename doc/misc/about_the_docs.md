# About the EEG-notebooks Documentation Pages

A few comments on how these are put together: 

The documentation pages are written for the following readthedocs sphinx-based setup:

- `readthedocs` auto-generates the documentation, using various configuration files 
- In particular, we use [Nbsphinx](https://github.com/spatialaudio/nbsphinx) to create `html` pages directly from a combination of jupyter notebooks, `.rst` files, and `.md` files
- Because the notebook files are not located under the docs folder, we additionally need to make use of [nbsphinx-link](https://github.com/vidartf/nbsphinx-link)


