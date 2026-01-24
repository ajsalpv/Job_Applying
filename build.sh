#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers and system dependencies
playwright install chromium
playwright install-deps chromium
