# Download script generator for QCD fragments for SVJ

The script requires `pip install minimal-cernsso` ( https://github.com/tklijnsma/minimal-cernsso).

1. Set up certificates as described in https://github.com/tklijnsma/minimal-cernsso#getting-certificate-files

2. Run `cernsso-get-cookies https://cms-pdmv.cern.ch/mcm/search -c path/to/myCert.pem -k path/to/myCert.key`

3. Run `python get.py`

4. Copy the generated `download_fragments.sh` into any CMSSW distribution and run it
