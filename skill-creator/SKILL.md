---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
- Rewrite the skill based on feedback from the user's evaluation of the results
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

## Core Loop

1. Figure out what the skill is about
2. Draft or edit the skill
3. Run the skill on test prompts
4. Evaluate the outputs with the user
5. Improve based on feedback
6. Repeat until satisfied
7. Package the final skill

## Creating a Skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first.

1. What should this skill enable the agent to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works?

### Write the SKILL.md

Based on the interview, fill in these components:

- **name**: Skill identifier (lowercase, hyphens/underscores)
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. Make descriptions slightly "pushy" to improve triggering.
- **compatibility**: Required tools, dependencies (optional)
- **body**: Markdown instructions

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

### Skill Writing Tips

- Keep SKILL.md under 500 lines; if approaching this limit, add additional layers
- Prefer imperative form in instructions
- Explain the **why** behind requirements - today's LLMs have good theory of mind
- Avoid heavy-handed MUSTs; explain reasoning so the model understands the intent
- Look for repeated work across test cases that should be bundled as scripts

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user for confirmation, then run them.

Save test cases to `evals/evals.json`:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

## Improving a Skill

After running test cases and receiving user feedback:

1. **Generalize from the feedback** — don't overfit to specific examples
2. **Keep the prompt lean** — remove things that aren't pulling their weight
3. **Explain the why** — try hard to explain the reasoning behind requirements
4. **Bundle repeated work** — if all test cases wrote similar scripts, the skill should bundle them

### The Iteration Loop

1. Apply improvements to the skill
2. Rerun all test cases
3. Launch the reviewer for user feedback
4. Read feedback, improve again, repeat

Keep going until:
- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines when the agent invokes a skill. After creating or improving a skill, consider optimizing the description for better triggering accuracy.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

For **should-trigger** queries (8-10): different phrasings of the same intent, some formal, some casual. Include cases where the user doesn't explicitly name the skill but clearly needs it.

For **should-not-trigger** queries (8-10): the most valuable ones are near-misses — queries that share keywords or concepts with the skill but actually need something different.

Bad: `"Format this data"`, `"Extract text from PDF"`
Good: `"my boss sent me this xlsx file (called 'Q4 sales final v2.xlsx') and wants me to add a column showing profit margin as a percentage. Revenue in column C, costs in column D"`

### Step 2: Run the optimization loop

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

### Step 3: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter.

## Reference

This skill is adapted from the skill-creator framework for iterative skill development.
