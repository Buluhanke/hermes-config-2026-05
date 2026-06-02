# Direction B — New Papers (2026-06-03 scan)

## A11y-Compressor (arXiv 2605.00551, May 2026)
- **Title**: A Framework for Enhancing the Efficiency of GUI Agent Observations through Visual Context Reconstruction and Redundancy Reduction
- **Institution**: Hosei University
- **Env**: Desktop
- **Key innovation**: Linearized accessibility-tree → compact structured representation; input tokens to 22% of original
- **Result**: OSWorld task success rate +5.1pp average
- **Hermes relevance**: screen_trigger AX-tree observation compression (tokens saving + accuracy improvement)

## WindowsWorld (arXiv 2604.27776, Apr 2026)
- **Title**: WindowsWorld: A Process-Centric Benchmark of Autonomous GUI Agents in Professional Cross-Application Environments
- **Institution**: HIT-Shenzhen
- **Env**: Desktop
- **Key stats**: 181 tasks, avg 5.0 sub-goals, 78% multi-application
- **Finding**: Existing computer-use agents <21% success on multi-application tasks
- **Hermes relevance**: Cross-application workflow coordination evaluation benchmark

## uxCUA (arXiv 2604.26020, Apr 2026)
- **Title**: Training Computer Use Agents to Assess the Usability of Graphical User Interfaces
- **Institution**: UW + Purdue
- **Env**: General GUI
- **Focus**: Usability evaluation of GUIs by computer-use agents
- **Hermes relevance**: Complements GUIDE Benchmark (user behavior understanding)

---

# Direction C — New CVEs (2026-06-03 scan)

## CVE-2026-44287 — FastGPT RCE
- **Target**: FastGPT AI Agent building platform (< 4.15.0-beta1)
- **Type**: RCE (Remote Code Execution)
- **Source**: NVD / ddgs search
- **Status**: Fixed in 4.15.0-beta1
- **Hermes relevance**: Non-direct (FastGPT not a Hermes dependency) but AI Agent platform class vulnerability worth monitoring
