# Security Policy

## Reporting a vulnerability

Report privately through GitHub's
[Security Advisories](https://github.com/sanketdaru/india-crypto-tax-calculator/security/advisories/new)
form. Please do **not** open a public issue for a security problem.

Do not include a real export, report, or any personal data in your report.

## What to expect

This is a personal project maintained on a best-effort basis. There is **no
response time commitment and no SLA**. Reports are read and acted on when the
maintainer has time. If a fix is warranted it will be released as a normal
commit with credit to the reporter, unless you ask otherwise.

## Scope

The calculator runs entirely on your own machine. It opens no network
connections, requires no account or API key, and transmits nothing anywhere. The
realistic threat model is therefore narrow:

**In scope**

- Anything causing the tool to write, log or transmit your transaction data
  outside the output file you asked for
- Malicious content in a crafted `.xlsx` leading to code execution
- A dependency with a known vulnerability that this project actually reaches

**Out of scope**

- Incorrect P&L figures. Those are bugs — open a normal issue.
- Anything requiring an attacker to already have access to your machine.
