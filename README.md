# Centris
Centris is a tool for identifying open-source components.
Specifically, Centris can precisely and scalably identify components even when they were reused with code/structure modifications.
Principles and experimental results are discussed in our [paper](https://ccs.korea.ac.kr/publication/) (will be added), 
which will be published in 43rd International Conference on Software Engineering (ICSE'21).

## How to use
### Prerequisites
* ***Linux***: Centris is designed to work on any of the operating systems. However, currently, this repository only focuses on the Linux environment. Centris can be operated on Windows if only some minor environment settings (e.g., the path of ctags parser used in OSSCollector) are changed.
* ***Python 3***
* ***[Universal-ctags](https://github.com/universal-ctags/ctags)***: for function parsing.
* ***[Python-tlsh](https://pypi.org/project/python-tlsh/)***: for function hashing.

### Running Centris
#### OSSCollector (src/dataset/)

1. Collect git clone URLs (will become the OSS dataset) into a file, as shown in the [sample](https://github.com/WOOSEUNGHOON/Centris-public/blob/main/src/dataset/sample) file.
The full list of OSS datasets used in the paper is shown in [here](https://github.com/WOOSEUNGHOON/Centris-public/blob/main/src/dataset/OSS%20Repository%20List%20(used%20in%20the%20paper)).

