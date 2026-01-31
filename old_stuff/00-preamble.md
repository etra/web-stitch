# Preamble

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

**Project name:** Web-Stitch
**Repository root:** `web-stitch/`
**Main Python package:** `stitch/`

The repository root (`web-stitch/`) contains all working files like `requirements.txt`, `.gitignore`, `migrations/`, and `tests/`.

The main Python package is `stitch/`, which contains the Flask application, models, services, and all backend logic.

**Import pattern:** `from stitch import create_app`
