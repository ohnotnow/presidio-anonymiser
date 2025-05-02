# Presidio Anonymiser

A command-line tool that reads text from a file, analyzes it for PII entities using [Microsoft Presidio Analyzer](https://microsoft.github.io/presidio/) (via Docker), and then anonymizes those entities using Presidio Anonymizer.

Repository URL
https://github.com/ohnotnow/presidio-anonymiser

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Presidio Services](#running-presidio-services)
- [Usage](#usage)
- [Options & Flags](#options--flags)
- [Example](#example)
- [License](#license)

## Features
- Detects PII entities (names, phone numbers, email addresses, etc.)
- Configurable anonymization operators (replace, mask, redact)
- Default fallback to `<ENTITY>` replacement
- Simple CLI interface

## Prerequisites
- Git
- Python 3.7+
- Docker
- Microsoft Presidio Analyzer & Anonymizer containers (see below)
- (Optional) `uv` CLI tool for dependency management and execution

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/ohnotnow/presidio-anonymiser.git
cd presidio-anonymiser
```

### 2. Install `uv` (if not already installed)
`uv` is a modern Python CLI task runner that will install dependencies and run your scripts.
See https://docs.astral.sh/uv/ for more details.

macOS & Ubuntu
```bash
python3 -m pip install --user uv
```

Windows (PowerShell)
```powershell
py -3 -m pip install --user uv
```

### 3. Install project dependencies
All required Python packages are declared in the project.
```bash
uv sync
```

> If you prefer not to use `uv`, you can manually install dependencies:
> ```bash
> python3 -m pip install requests
> ```

## Running the tool (Easy mode)
To do a quick run you can use the `run.sh` script which takes care of the docker side and running the script.

```bash
./run.sh /path/to/a/text/file.md
# or
./run.sh /path/to/a/directory_of_files/
```
That will pull the docker images (if you don't have them) and run the containers (if they're not already running) and anonymise the file(s).  The results will be printed to stdout.

## Running the tool (Hard mode)
### Running Presidio Services
You must have two Docker containers running locally:

1. **Presidio Analyzer** on port `5002`
2. **Presidio Anonymizer** on port `5001`

```bash
# Analyzer
docker run -d --rm -p 5002:5002 mcr.microsoft.com/presidio-analyzer:latest

# Anonymizer (default container port is 3000, map to 5001)
docker run -d --rm -p 5001:3000 mcr.microsoft.com/presidio-anonymizer:latest
```

### Usage
```bash
uv run main.py --text-file <input_file> [--lang LANGUAGE] [--threshold SCORE]
# or
uv run main.py --text-path <path-to-directory-of-files> [--lang LANGUAGE] [--threshold SCORE]
```

- `<input_file>`: Path to a text file containing the text to process
- `--lang`: ISO 639-1 language code (default: `en`)
- `--threshold`: Minimum confidence score for detections (0.0–1.0, default: `0.5`)
- `--quiet`: Suppress most 'info' style messages

### Direct invocation (without `uv`)
```bash
python3 main.py --text-file input.txt --lang en --threshold 0.7
```

## Options & Flags
  - `--lang`
    Language code for analysis (e.g. `en`, `es`).
  - `--threshold`
    Float between 0 and 1. Only entities with a confidence ≥ threshold will be returned.

All configuration of anonymization operators is done in `main.py` under the `anonymizers` dict:
```python
anonymizers = {
    "DEFAULT":       { "type": "replace", "new_value": "ANONYMIZED" },
    "PHONE_NUMBER":  { "type": "mask",    "masking_char": "*", "chars_to_mask": 4, "from_end": True },
    "EMAIL_ADDRESS": { "type": "redact" }
}
```

## Example
```bash
uv run main.py --text-file sample_input.txt --lang en --threshold 0.6
```
Output:
```
[+] Loaded 324 characters from 'sample_input.txt'
[+] Sending to Presidio Analyzer...
[+] Detected 3 PII entities:
    - EMAIL_ADDRESS at [10–25] (score=0.95)
    - PHONE_NUMBER at [45–55] (score=0.88)
    - PERSON at [100–108] (score=0.77)
[+] Sending to Presidio Anonymizer...

=== Anonymized Text ===
Hello ANONYMIZED, your phone number ****** is now protected. Please contact ANONYMIZED for details.
========================
```

## License
This project is licensed under the MIT License.
