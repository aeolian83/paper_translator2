# Dataset Generation
Data synthesis using this Multi-Agent must be conducted in an environment different from the main application’s runtime environment. Since it requires Python 3.10, it is recommended to use a separate virtual environment.

## Conda environment
```bash
conda create -n autogen python=3.10
```

## .env Settings
```
HF_TOKEN = 'api_key'
OPENAI_API_KEY = 'api_key'
```

## Dependency Install 
```bash
pip install -r requirements.txt
```