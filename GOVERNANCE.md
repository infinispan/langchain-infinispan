# Project Governance

## Project Overview
This project is maintained by the Infinispan team to provide a LangChain integration for Infinispan's vector store capabilities.
We operate on consensus-based decision-making with clear processes for contribution and growth.

## Team Structure

### Core Maintainers
**Lead Maintainer**: [Vittorio Rigamonti] (@rigazilla)
- **Responsibilities**: Final decision tiebreaker, release coordination, project direction
- **Contact**: vittorio@infinispan.org

**Community Maintainer**: [Katia Aresti] (@karesti)
- **Responsibilities**: Community engagement, contributor onboarding, developer experience
- **Contact**: katia@infinispan.org

### Maintainer Responsibilities
All maintainers share:
- Code review duties
- Issue triage and community support
- Release testing and validation
- Project roadmap planning
- New contributor mentoring

## Decision-Making Process

### Consensus Decisions (All maintainers must agree)
- Breaking API changes (InfinispanVectorStore, InfinispanClient, DistanceStrategy)
- Adding new maintainers
- Changing governance structure
- License changes
- Major dependency updates (e.g. langchain-core major version)

### Individual Authority
Any maintainer can:
- Merge bug fixes and minor improvements
- Respond to issues and questions
- Update documentation
- Perform routine maintenance (dependency updates, CI fixes)

### Decision Timeline
- **Standard Decisions**: 1 week discussion period
- **Major Changes**: 2 week discussion
- **Emergency Fixes**: 24-48 hours with post-hoc review

## Communication Channels

### Community
- **Issues**: Bug reports, feature requests
- **Pull Requests**: Code contribution discussions
- **Chat**: [Infinispan Zulip](https://infinispan.zulipchat.com/)
- **Email**: maintainers@infinispan.org for private matters

## Contribution Process

### New Contributors
1. **First Contribution**: Single maintainer approval for small fixes
2. **Regular Contributors**: After 3+ quality contributions, eligible for expanded review privileges
3. **Contributor Recognition**: Public acknowledgment

### Becoming a Maintainer
Requirements:
- 6+ months of consistent, quality contributions
- Deep understanding of the project and the LangChain ecosystem
- Positive community interactions
- Availability for ongoing responsibilities
- Unanimous approval from existing maintainers

Process:
1. **Nomination**: Any maintainer can nominate a contributor
2. **Discussion**: 2-week private maintainer discussion
3. **Vote**: Unanimous approval required
4. **Invitation**: Private invitation with role explanation
5. **Onboarding**: Mentorship period

## Release Process

### Release Types
- **Patch**: Bug fixes, minor improvements (any maintainer)
- **Minor**: New features, non-breaking changes (2+ maintainer approval)
- **Major**: Breaking changes, major features (all maintainer approval)

### Release Checklist
1. All tests pass (unit + integration)
2. CHANGELOG.md updated
3. Version bumped in `pyproject.toml`
4. Documentation updated
5. Published to PyPI
6. GitHub release created
7. Community announcement

## Code Quality Standards
- **Test Coverage**: Unit tests for all new logic, integration tests for REST API interactions
- **Code Review**: At least 1 maintainer approval for all changes
- **Type Hints**: Required for all function signatures
- **Linting**: Must pass ruff checks

## Code of Conduct
This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). All maintainers are responsible for enforcement.

## Contact Information
- **General Inquiries**: maintainers@infinispan.org
- **Security Issues**: security@infinispan.org
- **Code of Conduct**: conduct@infinispan.org

---
*This governance structure will be reviewed periodically for effectiveness and necessary adjustments.*
