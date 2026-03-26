---
title: "Security"
description: "How to report security vulnerabilities in llmdocs responsibly."
category: "Community"
order: 52
tags: [security, disclosure]
---

# Security

## Reporting a vulnerability

If you believe you’ve found a **security issue** (e.g. path traversal, auth bypass, remote code execution in default deployment):

1. **Do not** open a public issue with exploit details.
2. **Contact the maintainers privately** — use GitHub **Security Advisories** for this repository if enabled, or email the maintainer if published in the repo profile.

Include:

- Affected version or commit.
- Minimal reproduction steps.
- Impact assessment if you can.

## Scope

Default deployment is **self-hosted** with **no authentication** on HTTP/MCP — treat that as **expected** for v1; securing the edge (reverse proxy, VPN, firewall) is the operator’s responsibility.

## Disclosure

We aim to acknowledge reports and coordinate a fix and release timeline; public disclosure should follow a fix when possible.
