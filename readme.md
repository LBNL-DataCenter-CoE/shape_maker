# Shape Maker: Data Center and Industrial Electrical Load Shape Generator

This repo contains the data center and industrial electrical load Shape Maker. The Shape Maker allows users to generate hypothetical electricity loads capturing the key characteristics around variability, diurnal patterns, and load factors while including randomness that reflects real demands. The tool creates a custom time step annual electrical load shape time series based on a set of input parameters. It comprises a daily and an annual load shape generator. The daily shapes, defined for weekdays and weekends, allow for variation in the base and peak load, marginal noise, and number, slope, start and duration of the peaks. The annual load shapes comprise daily load shapes parametrized for day-to-day variation. A broad range of different load shapes can be represented using these general concepts. The load components can have differing shapes, e.g. a flat shape for always-on indoor lighting, and more variable shapes for the loads driven by computational demand.

The tool enables disaggregation of the load shape into various components of power demand. For data center applications, those are IT load components, the power distribution, and the lighting. The disaggregation weights and shapes vary by data center type and application.

The tool has initially been developed to synthesize data center facility electrical load shapes. With custom user inputs, the use cases expand to industrial facilities, building loads, or any electrical demands. The load shapes are indispensable in grid and facility level design and planning, and this tool generates quick sample load shapes, or entire load shape “libraries” to use in modeling.

Data center and industrial electricity load shapes are not yet readily available to research and development. The Shape Maker tool aims to bridge that gap by generating synthetic parametric load shapes for a wide range of industrial applications. The load shapes are defined based on the observation of the accessible metered data, and, where available, were vetted by a number of industry experts.

## Overview and Purpose

Data centers impose a growing demand on the electrical grid. The industrial sector consumes roughly a third of the nation’s electricity. The energy consumption is intermittent in its nature. Therefore, knowledge about the load shape timeseries can help ensure abundant, reliable, and resilient energy supply, as well increase the facility planning effectiveness and reduce the associated risks.

Shape Maker is a Python-based synthetic load profile generation tool developed to produce realistic, parametric annual electrical load time series for data centers and industrial facilities. Originally developed at Lawrence Berkeley National Laboratory's Center of Expertise for Data Center Energy, the tool addresses a critical gap in the energy research and planning ecosystem: the lack of readily available, high-fidelity electricity load shape data for data centers and industrial consumers. Rather than relying on proprietary metered data that is difficult to obtain and share, Shape Maker generates synthetic load profiles grounded in physical observation and validated by industry expertise, enabling a wide range of users to conduct meaningful energy analysis without access to sensitive operational data.

The tool is organized around six core functions, each handling a distinct layer of the load generation process:

- `logistic_function` — a sigmoid function used to produce smooth, physically realistic ramp transitions between load levels
- `generate_daily_load_profile` — constructs a single day's load time series from a baseline, peak parameters, and noise
- `generate_yearly_load_profile` — assembles a full annual time series by iterating daily profiles across weekdays, weekends, and holidays
- `correct_l0` — back-calculates the true baseline load needed to hit a user-specified annual average, accounting for diurnal peak contributions
- `generate_specific_it_load_profiles` — produces IT load profiles using a library of predefined noise and diurnal style combinations
- `create_power_components_dataset` — disaggregates the aggregate IT load into individual power components such as processors, fans, and distribution losses

The tool's primary output is a timestamped annual time series expressed as a fraction of nominal IT capacity, which can be scaled to any facility size. The combination of flexibility, physical realism, and computational efficiency makes Shape Maker suitable for rapid scenario generation, techno-economic analysis, and large-scale load shape library construction.


## Modeling Approach and Methodology

At the foundation of the tool is a two-level generative architecture: a daily load profile generator and an annual load profile assembler that iterates over each day of the year, constructing the full time series from daily building blocks. Each daily profile is controlled by a rich set of parameters:

- **Base load level (l0)** — the minimum continuous facility draw, around which all variation is defined
- **Peak parameters** — each peak is defined by a start time, a duration, and a part-load fraction, with support for multiple peaks per day
- **Noise** — a uniformly distributed random variation added at every time step, scaled as a percentage of the base load
- **Transition duration and smoothness** — control the steepness and length of the logistic ramp between baseline and peak, enabling everything from sharp step-like switching to gradual behavioral shifts
- **Weekday/weekend differentiation** — separate peak timing windows, load levels, and frequency distributions are applied depending on the day type
- **Holiday handling** — recognized U.S. federal holidays are automatically treated as weekend-type days

The annual generator iterates day by day, with day-to-day variability in noise intensity modulated within a minimum-to-maximum band, producing a natural heterogeneity across the annual calendar consistent with real facility operations. A mathematically important correction is applied when the user specifies a target annual average load fraction rather than a raw baseline: the `correct_l0` function back-calculates the true baseline needed such that, after accounting for all diurnal peak contributions over weekdays and weekends throughout the year, the time-averaged load equals the intended value. This ensures that users can specify an intuitive annual utilization target and receive a physically consistent load series without needing to manually solve for the underlying baseline parameter.

## Power Component Disaggregation

Beyond the aggregate IT load time series, Shape Maker provides a disaggregation framework that decomposes the total facility electrical demand into individual power flow components through the `create_power_components_dataset` function. Three classes of components are supported:

- **IT load components** — sub-elements of the IT load that scale proportionally with total IT demand, including server processors (CPUs and GPUs, 75% of IT load), server fans (10%), other server components (10%), and miscellaneous IT equipment such as storage and networking (5%). For liquid-cooled facilities, fan power is eliminated and the remaining components are rescaled accordingly.
- **Flat loads** — fixed quantities expressed as a percentage of nominal IT capacity regardless of instantaneous utilization, with lighting as the primary example, ranging from 0.1% of IT capacity for large facilities to 1% for small ones
- **Load-following efficiency losses** — overhead from power conversion infrastructure that scales with IT load, principally power distribution losses (default 90% efficiency) and UPS losses (default 95% efficiency), each contributing a proportional overhead term to the total facility draw

The resulting dataset contains a column for each power component plus a total column, and can be exported to CSV for use in downstream modeling tools. Users can optionally scale all values by a nominal IT capacity in megawatts to convert from normalized fractions to absolute power quantities.

## Predefined Load Shape Archetypes

To streamline use for data center applications, Shape Maker provides a library of predefined load shape archetypes accessible through the `generate_specific_it_load_profiles` function. These archetypes are constructed from combinations of two orthogonal parameter dimensions: noise level and diurnal pattern.

Noise level captures the degree of short-term variability in the load signal, with two options available: **low noise** (3–7% of baseline), reflecting large, highly aggregated facilities whose statistical pooling smooths moment-to-moment fluctuations, and **high noise** (12–18% of baseline), reflecting smaller or more specialized facilities with more volatile demand.

Diurnal pattern defines the time-of-day shape of the load, with five styles available:

- **Flat** — no meaningful time-of-day variation, characteristic of large AI training clusters running continuous batch jobs
- **Business diurnal** — a moderate 10%-above-baseline peak during business hours (8 AM–5 PM) on weekdays, reflecting enterprise inference workloads that track human working schedules
- **Business high diurnal** — an amplified 35%-above-baseline daytime weekday peak, capturing more extreme office-hours demand concentration
- **Customer diurnal** — a moderate evening peak (4–9 PM) on both weekdays and weekends, modeling facilities whose load tracks consumer internet activity
- **Customer high diurnal** — an amplified version of the customer diurnal pattern at 35% above baseline

These diurnal and noise styles are cross-applied to a parameter table of data center configurations spanning three dimensions of facility type:

- **Size** — large, medium, or small
- **Usage type** — inference, training, or mixed workloads
- **Cooling fluid** — air or water

The combination of two noise styles, five diurnal patterns, and fifteen data center types produces a library of up to 90 distinct annual load profiles, each generated as a 15-minute resolution time series spanning a full calendar year. This library can be populated in a single automated batch run and stored as a named collection for downstream analysis.

## Applications and Intended Users

Shape Maker is designed to serve a broad spectrum of technical and commercial applications. Because the parametric framework is not exclusive to data centers, users can adapt the tool to represent industrial manufacturing loads, commercial building demands, or any electrical consumer whose behavior can be characterized by a baseline, periodic peaks, and stochastic noise. 

The tools can effectively be used in performing risk assessment, improving system and facility resilience, estimating grid flexibility potential, and more. The primary commercial and non-commercial Shape Maker use-cases are:

- **Grid planning** — Generating diverse, physically grounded load shape inputs to study grid reliability, capacity needs, and resilience under different facility growth scenarios;
- **Techno-economic analysis** — Industrial and commercial sectors can utilize the tool to support innovation via techno-economic analysis (TEA) and risk analysis (RA), streamline the grid connection processes for new facilities, and optimize the upfront and operating costs; 
- **Workload and flexibility assessment** — modeling counterfactual operating scenarios, evaluating workload shifting potential, and quantifying demand response capacity available to grid operators. Data center operators can leverage the tool in managing and distributing workloads;
- **Research and development** — Universities and National Labs can use the tool for a broad range of topics, from performing long term grid planning to the development of new technologies, including risk assessment

The modular function structure and clear parameter interfaces make extension and customization straightforward for users with basic Python proficiency, and the tool is distributed with a standard virtual environment installation process and optional editable installation mode for developers.

---
Installation Instructions
------------------

Create a virtual environment:

`python -m venv venv`

Activate the venv:

`source venv/bin/activate`

On Windows, use

`venv\Scripts\activate`

Install in isolated mode

`pip install .`

Or, install in editable mode

`pip install -e .`

---

## Contributing

Create an issue and describe your contribution idea. One of the developers may respond with opinion, advice and guidance for any next steps.

---

## Acknowledgements

This software was initially developed in the scope of the DOE Cold UTES project.

## Team

The codebase was developed at Lawrence Berkeley National Lab, Energy Technologies Area by Sarah Smith, Milica Grahovac, Alex Newkirk, Evan Neill, Vlada Dementyeva and others.

## Copyright

Data Center and Industrial Electricity Load Shape Maker (Shape Maker) 
Copyright (c) 2026, The Regents of the University of California, through
Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Intellectual Property Office at
IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department
of Energy and the U.S. Government consequently retains certain rights.  As
such, the U.S. Government has been granted for itself and others acting on
its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the
Software to reproduce, distribute copies to the public, prepare derivative 
works, and perform publicly and display publicly, and to permit others to do so.
