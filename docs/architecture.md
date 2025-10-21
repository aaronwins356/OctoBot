# Architecture

OctoBot is organised into constitutional subsystems. The following highlights the most important modules:

## octobot.connectors

Connector interfaces for OctoBot.

## octobot.connectors.unreal_bridge

Thin REST connector for the Chat Unreal reasoning service.

## octobot.connectors.utils

Common helpers for hardened connector implementations.

## octobot.connectors.web_crawler

Documentation crawler leveraging the Chat Unreal bridge.

## octobot.core

Government package for OctoBot governance modules.

## octobot.core.compiler

Compile evaluated proposals into summary artifacts.

## octobot.core.evaluator

Proposal evaluation heuristics.

## octobot.core.orchestrator

Asynchronous event orchestrator for proposal lifecycles.

## octobot.core.proposal_manager

Proposal management for OctoBot.

## octobot.core.updater

Apply approved proposals.

## octobot.interface

Interface layer for OctoBot.

## octobot.interface.cli

Command line interface for supervising OctoBot.

## octobot.interface.dashboard

FastAPI dashboard exposing proposal lifecycle data.

## octobot.laws

Governance rules for OctoBot.

## octobot.laws.audit

Compliance auditing helpers.

## octobot.laws.validator

Central law loading and runtime enforcement.

## octobot.memory

Memory subsystem for OctoBot.

## octobot.memory.history_logger

Database-backed storage for OctoBot state.

## octobot.memory.ledger

Append-only cryptographic ledger for proposals.

## octobot.memory.logger

Structlog-backed logging utilities for OctoBot.

## octobot.memory.reflector

Aggregate operational logs into weekly reflection digests.

## octobot.memory.reporter

Analytics and reporting utilities for OctoBot.

## octobot.memory.utils

Utility helpers for persistent storage and path management.

## octobot.utils

Utility helpers for OctoBot.

## octobot.utils.yaml

Minimal YAML helper with optional PyYAML support.
