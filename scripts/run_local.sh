#!/bin/bash
source venv/bin/activate
export PYTHONPATH=$(pwd)
python src/lambda_functions/get_prices_lambda/scraper.py
