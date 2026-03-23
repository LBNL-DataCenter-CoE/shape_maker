Shape Maker
===========

This repo contains the data center and industrial electrical load Shape Maker. The Shape Maker allows users to generate hypothetical electricity loads capturing the key characteristics around variability, diurnal patterns, and load factors while including randomness that reflects real demands. The tool creates a custom time step annual electrical load shape time series based on a set of input parameters. It comprises a daily and an annual load shape generator. The daily shapes, defined for weekdays and weekends, allow for variation in the base and peak load, marginal noise, and number, slope, start and duration of the peaks. The annual load shapes comprise daily load shapes parametrized for day-to-day variation.

The tool enables disaggregation of the load shape into various components of power demand. For data center applications, those are IT load components, the power distribution, and the lighting. The disaggregation weights and shapes vary by data center type and application.

The tool has initially been developed to synthesize data center facility electrical load shapes. With custom user inputs, the use cases expand to industrial facilities, building loads, or any electrical demands. The load shapes are indispensable in grid and facility level design and planning, and this tool generates quick sample load shapes, or entire load shape “libraries” to use in modeling.


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

User Guide
----------

Data centers impose a growing demand on the electrical grid. The industrial sector consumes roughly a third of the nation’s electricity. The energy consumption is intermittent in its nature. Therefore, knowledge about the load shape timeseries can help ensure abundant, reliable, and resilient energy supply, as well increase the facility planning effectiveness and reduce the associated risks.

Data center and industrial electricity load shapes are not yet readily available to research and development. The Shape Maker tool aims to bridge that gap by generating synthetic parametric load shapes for a wide range of industrial applications. The load shapes are defined based on the observation of the accessible metered data, and, where available, were vetted by a number of industry experts.

A broad range of different load shapes can be represented by the general concepts described in the abstract (diurnal shapes, daily variation, hourly noise centered around a defined baseline load). The load components can have differing shapes, e.g. a flat shape for always-on indoor lighting, and more variable shapes for the loads driven by computational demand.

The primary commercial and non-commercial uses of the Shape Maker are:
Universities and national laboratories can use the tool for a broad range of topics, from performing long term grid planning to the development of new technologies, including risk assessment, Industrial and commercial sectors can utilize the tool to support innovation via techno-economic analysis (TEA) and risk analysis (RA), streamline the grid connection processes for new facilities, and optimize the upfront and operating costs. For instance, once the data center layout and nominal IT power are known, the planners can utilize the shape maker to generate an array of load shapes to inform the TEA and RA
Data center operators can leverage the tool in managing and distributing workloads.
The tools can effectively be used in performing risk assessment, improving system and facility resilience, estimating grid flexibility potential, and more.

## Contributing

Create an issue and describe your contribution idea. One of the developers may respond with opinion, advice and guidance for any next steps.

## Acknowledgements

This software was initially developed in the scope of the DOE Cold UTES project.

## Team

The codebase was developed at Lawrence Berkeley National Lab, Energy Technologies Area by Sarah Smith, Milica Grahovac, Alex Newkirk, Evan Neill, Vlada Dementyeva and others.
