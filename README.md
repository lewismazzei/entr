# EntR

A markup language for ER diagrams.

<!-- black badge -->

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

1. Install graphviz

   `brew install graphviz`

2. Clone the Repo

   `git clone https://github.com/lewismazzei/entr.git`

3. Change Directory

   `cd entr`

4. Create and activate virtual environment

   `python3 -m venv venv`

   `source venv/bin/activate`

5. Install dependencies

   `pip install -r requirements.txt`

## Usage

1. Change directory

   `cd program`

2. Run

   `python entr.py <input_filepath>`

The generated `.dot` and `.png` files will be placed in the `/dot` and `/png` directories respectively.
