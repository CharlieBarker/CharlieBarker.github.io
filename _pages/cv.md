---
layout: archive
title: "CV"
permalink: /cv/
author_profile: true
redirect_from:
  - /resume
---

{% include base_path %}

Employment
======
* 2025–2026: Postdoctoral Researcher, Team VPE (Virtual Patient Engine), in partnership with Sanofi
  * Building an AI-driven virtual patient platform to predict drug efficacy in chronic immune-mediated diseases (atopic dermatitis, IBD)
  * Analysing longitudinal clinical multi-omics (bulk/scRNA-seq, O-link proteomics) to model disease trajectories and treatment response
  * Developing QSP surrogates with time-series and protein language foundation models for regimen-aware forecasting in virtual patients

* 2022–2025: Research Fellow in Computational Biology, UCL
  * Supervisor: Prof. Jasmin Fisher
  * Designed graph neural networks (MAGELLAN) to automate generation of mechanistic, interpretable models from multi-omics data
  * Built visualisation tools (biotubemapR, volcanoPlus) for multi-modal pathway and differential expression analysis
  * Led collaborations with wet-lab biologists to validate predictions of drug resistance and combination therapies in NSCLC and melanoma

Education
======
* 2018–2022: Ph.D. Biological Sciences, EMBL-EBI / University of Cambridge
  * Supervisor: Dr. Evangelia Petsalaki
  * Pipelines integrating imaging and bulk/single-cell RNA-seq to derive phenotype-specific signalling networks
* 2014–2018: MSci Biochemistry
  * Undergraduate training in computational and structural biology (antibody CDR-H3 modelling via abYmod and RIPPER ML)

Skills
======
* **Computational modelling:** hybrid AI models, QSP, graph-based and mechanistic modelling, structural modelling
* **Statistical analysis:** regression, clustering, dimensionality reduction, survival analysis, trajectory inference
* **ML/AI:** PyTorch, GNNs, LLMs, protein/textual embedding models, time-series foundation models, explainable ML
* **Omics analysis:** bulk and scRNA-seq, phosphoproteomics, proteomics (O-link), ATAC-seq, NGS, imaging
* **Programming:** Python, R, Bash, Unix, LaTeX, Git; HPC environments
* **Deployment and collaboration:** AWS, Docker, Nextflow, CI/CD, Conda, Jupyter, RShiny, unit testing

Publications
======
  <ul>{% for post in site.publications reversed %}
    {% include archive-single-cv.html %}
  {% endfor %}</ul>

Talks
======
  <ul>{% for post in site.talks reversed %}
    {% include archive-single-talk-cv.html  %}
  {% endfor %}</ul>

Teaching
======
  <ul>{% for post in site.teaching reversed %}
    {% include archive-single-cv.html %}
  {% endfor %}</ul>

Awards and service
======
* 2025: Runner-up, City of London CRUK Datathon (AI-driven AML outcome prediction)
* 2023: Selected EMBL representative, 72nd Lindau Nobel Laureate Meeting
* 2022: Early Career Research Award, British Society for Proteome Research Conference
* 2019–2020: PhD Representative, EMBL-EBI
