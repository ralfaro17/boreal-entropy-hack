#!/usr/bin/env bash

# # 1. Install frontend dependencies
# cd ../frontend
# pnpm install

# 2. Install backend dependencies (automatically creates .venv using uv.lock)
cd ../backend
uv sync