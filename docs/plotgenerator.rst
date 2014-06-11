.. _plotgenerator:

**********************
Dynamic Plot Generator
**********************

An important desing concept of HappyFace is saving a long-term history of monitoring data, so that events (e.g. software failure or dead-locks) can be analyzed for time correlation with other events. Instead of looking on tables of data, looking at a visual representation often yields a better understanding. As an example, the number of cache transfers increses at the same time as the response time decreases.

Because looking at the raw data in image form is a recurring requirement in HappyFace, it provides the so called plotgenerator for generating graphs. It cannot only be used by modules to generate images, but with a comfortable web interface site users can generate plots on their own.

.. todo: How do we use the plot generator?

.. _column_expressions:

Column expression layout
========================
Test