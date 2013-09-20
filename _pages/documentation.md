---
title: Document Center
---

## Goals

Build and test private cloud with minimum time possible

## Principles

-   Single command line utility

-   All builds are config files (json, yaml&#x2026;)

    -   including arguments

-   Plugin architecture - Extensibility

    -   independent of provisioning tools or environment

    -   API first

-   Follow python coding guidlines

    -   peer-review

    -   gating - gerrit, flake8

-   Ability to scale

    -   Two node deployment vs 20 node deployment

-   "Do it with right with minimum code execution time possible"

## Features

-   Front end possible

-   Standard python logging

-   Test framework - tempest

    -   performance data

    -   metrics

    -   graphs

    -   failures

-   Parallel running possible
	 <https://github.com/pkittenis/parallel-ssh>

# ORM

![nil](class.png)
