# GUIrilla: A Scalable Framework for Automated Desktop UI Exploration

- **arXiv**: 2510.16051 (v2, 24 Mar 2026)
- **Workshop**: DATA-FM @ ICLR 2026
- **Authors**: Sofiya Garkot, Maksym Shamrai, Ivan Synytsia, Mariya Hirna

## What It Is

A **data crawling framework** for automated exploration of desktop GUIs — NOT an autonomous agent.
Systematically collects realistic interaction traces and accessibility metadata to support training 
of downstream foundation models and GUI agents.

## Key Properties

- **macOS-first**: targets the largely underrepresented macOS platform
- **MacApp Trees**: hierarchical accessibility representations of macOS applications
  - Derived from accessibility states and user actions
  - Reusable structural representation for downstream analysis, retrieval, testing, agent training
- **Not an agent**: explicitly positioned as data infrastructure, not autonomous execution

## Open Source

- **Library**: `macapptree` (open-source)
- Full framework implementation released to support open research

## Relevance to Hermes

- **Directly applicable**: macOS-first data collection aligns with Hermes' macOS environment
- **MacApp Trees** could complement screen_watcher's screenshot-based approach with structured 
  accessibility metadata
- Training data source if Hermes moves toward fine-tuning or distillation
- Validates the approach of systematic desktop data collection for agent training
