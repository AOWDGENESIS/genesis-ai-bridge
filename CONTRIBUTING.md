# Contributing

Thank you for helping improve Genesis AI Bridge.

- Include a clear problem statement and reproducible steps.
- Never attach API keys, access tokens, passwords, private documents, or unredacted diagnostic logs.
- Keep the loopback-only web binding and explicit correction-confirmation flow intact.
- Add tests for archive traversal, symlinks, size/depth limits, source-change detection, and correction-path validation when changing those areas.
- Model output and file contents are untrusted data. Do not execute them as shell commands or Python code.
- Distinguish simulator/unit-test results from Windows VM and live-provider integration results.
- Do not claim a security guarantee based solely on passing automated tests.
- Do not publish a release until tests, security review, and release evidence have been checked.
