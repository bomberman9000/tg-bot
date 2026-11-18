# Logistics Telegram Bot — Backend Case Study

**Project type:** Telegram-based logistics workflow and API  
**Focus:** Python, PostgreSQL, Redis, FastAPI and bot integration  
**Source:** [GitHub repository](https://github.com/bomberman9000/tg-bot)

## Problem

Logistics users need a conversational interface for cargo search, inquiries and role-specific workflows, backed by durable application data.

## Repository scope

The README documents a Python/FastAPI service with Telegram bot handlers, database and Redis integration, roles for shippers, carriers and forwarders, administrative UI and an optional AI-assisted `/find` command.

## Architecture to inspect

- `main.py`: application startup
- `src/bot/`: Telegram handlers and state management
- `src/core/`: services, persistence and search logic
- `src/admin/`: administrative interface
- `migrations/`: database changes

## Safety and verification

`.env.example` contains sample-only credentials; they must not be reused in deployment. This document does **not** certify the current bot's live status, data safety, security or API reliability. Assess those separately with test infrastructure.

## Portfolio next steps

Add a synthetic Telegram conversation walkthrough, one architecture diagram and reproducible test/CI results before asserting production readiness.
