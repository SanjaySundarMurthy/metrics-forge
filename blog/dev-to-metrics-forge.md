---
title: "📊 metrics-forge: Generate Prometheus Rules & Grafana Dashboards from Service Definitions"
published: true
description: "A Python CLI tool that generates Prometheus alerting rules and Grafana dashboards from YAML service definitions with SLO-based burn rate alerting."
tags: prometheus, grafana, sre, monitoring
---

## What I Built

**metrics-forge** — define services with SLOs in YAML, get production-ready monitoring:

- **Service Tier-Aware Rules** — Critical/Standard/Best Effort with adjusted thresholds
- **SLO Burn Rate Alerting** — Fast burn + slow burn for availability SLOs
- **Grafana Dashboards** — Request rate, latency, CPU, memory, pod health panels
- **10 Validation Rules** — MET-001 to MET-010 for alert quality

## Test Results

```
43 passed in 0.41s
```

## Links

- **GitHub**: [metrics-forge](https://github.com/sanjaysundarmurthy/metrics-forge)
- **Part of**: DevOps CLI Tools Suite (Tool 9 of 14)
