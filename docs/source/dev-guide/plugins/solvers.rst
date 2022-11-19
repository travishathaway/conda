=======
Solvers
=======

The conda solvers can be extended with additional backends with the
``conda_solvers`` plugin hook. Registered solvers will be available
for configuration with the ``solver`` configuration and ``--solver``
command line option.

.. autoclass:: conda.plugins.types.CondaSolver
   :members:
   :undoc-members:

.. autofunction:: conda.plugins.hookspec.CondaSpecs.conda_solvers
