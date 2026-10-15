# Issue Creation Instructions

## Issue Types

Use GitHub issue labels for classification:

| Type        | When to Use                                                                 |
|-------------|-----------------------------------------------------------------------------|
| **Bug**     | Something is broken or behaving incorrectly                                 |
| **Feature** | New functionality or enhancement to existing functionality                  |
| **Task**    | Cleanup, refactoring, dependency updates, CI changes — not a bug or feature |

## Required Fields by Type

### Bug Report
- **Description** (required) — what is broken
- **Expected behavior** (required) — what should happen
- **Actual behavior** (required) — what happens instead
- **How to reproduce** (required) — steps, code snippet, or link to a reproducer
- **Environment** — Python version, Infinispan version, OS

Note: security vulnerabilities should be reported privately, not as public issues.

### Feature Request
- **Description** (required) — what the feature does and why it's needed
- **Implementation ideas** (optional) — technical approach

### Task
- **Description** (required) — what needs to be done
- **Implementation ideas** (optional) — technical approach

## Conventions

- Issue titles should be concise and descriptive
- Reference related issues and PRs using `#number` format
- When creating issues from code investigation, include file paths and line numbers where relevant
- Prefix commit messages with a short summary of the change

## External Resources

- **Infinispan documentation:** [infinispan.org](https://infinispan.org/)
- **LangChain documentation:** [docs.langchain.com](https://docs.langchain.com/)
- **Community chat:** [Infinispan Zulip](https://infinispan.zulipchat.com/)
- **Questions about Infinispan:** [StackOverflow (tag: infinispan)](https://stackoverflow.com/questions/ask?tags=infinispan)
