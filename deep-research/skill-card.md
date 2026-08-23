## Description: <br>
Seven-stage deep research pipeline for substantive research questions. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[9438190](https://clawhub.ai/user/9438190) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Employees, external users, developers, and research-oriented agents use this skill to plan, execute, and write evidence-backed long-form research reports in the user's language. It guides the agent through clarification, outline confirmation, sequential web research, completeness checks, Markdown report generation, and optional HTML rendering. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Broad research prompts may trigger a long, multi-stage research run. <br>
Mitigation: Review and confirm the generated outline before allowing the agent to continue into the full research workflow. <br>
Risk: Research outputs may include inaccurate or weakly supported findings if sources are incomplete or stale. <br>
Mitigation: Use the skill's source-diversity, citation, and completeness checks, and review cited evidence before relying on conclusions. <br>
Risk: Optional local report and HTML generation writes files into the workspace. <br>
Mitigation: Review generated files in reports/ before sharing or publishing them. <br>


## Reference(s): <br>
- [Deep Research skill page](https://clawhub.ai/9438190/skills/deep-research) <br>
- [HTML rendering guide](references/html-guide.md) <br>
- [Writing guide](references/writing-guide.md) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Code, Shell commands, Guidance] <br>
**Output Format:** [Conversational research updates, cited Markdown reports, and optional single-file HTML.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Reports are saved under reports/ as Markdown, with optional HTML rendering when the user confirms.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
