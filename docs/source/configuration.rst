.. _auto-config-reference:

=======================
Configuration reference
=======================

This page lists every documented conda setting with its type, default value,
aliases, and the environment variable that sets it. It is generated from the
settings defined in conda itself, so it always matches this version of conda.
Run ``conda config --describe`` to see the same information for the conda you
have installed.

For how to create and edit a ``.condarc`` file, see
:doc:`user-guide/configuration/use-condarc`. For the ``conda config`` command,
see :doc:`commands/config`. Worked examples for common tasks are on the
:doc:`user-guide/configuration/settings` page.

.. _config-how-settings-resolve:

How settings are resolved
=========================

Conda reads each setting from, in increasing order of precedence:

#. Configuration files, found as described in :ref:`condarc_search_precedence`.
   Files that are searched later override earlier ones.
#. Environment variables.
#. Command-line options, such as ``--channel`` or ``--override-channels``.

Environment variables
---------------------

Every setting that is a string, number, boolean, or list can be set with the
environment variable ``CONDA_<NAME>``, where ``<NAME>`` is the upper-case
setting name, for example ``CONDA_CHANNEL_PRIORITY``. Any alias of a setting
works the same way (``CONDA_ENVS_PATH`` for ``envs_path``).

* For boolean settings use ``true``/``false`` (and the usual variants such as
  ``yes``/``no`` or ``1``/``0``).
* For list settings, separate items with a comma, unless the entry says
  otherwise. ``pinned_packages`` and ``disallowed_packages`` use ``&`` and
  ``envs_dirs`` uses the path separator of your operating system.
* Settings that are maps (key/value pairs) can only be set in a configuration
  file; their entries below say ``Environment variable: not supported``.

Variable expansion
------------------

Where an entry says ``${VAR}`` is expanded, references to environment
variables in the value (``$VAR`` or ``${VAR}``) are replaced with their values
when the configuration is read.

Command line
------------

Use ``conda config --set NAME VALUE`` to set a setting, ``--add``,
``--prepend``, and ``--remove`` to change list settings, and
``conda config --show NAME`` to see the value currently in effect.

Plugin settings
---------------

Settings provided by plugins are named ``plugins.<name>`` and are set with
``CONDA_PLUGINS_<NAME>``. They depend on the plugins you have installed and are
not listed here; see :doc:`dev-guide/plugins/settings` for how plugins define
them.

Settings
========

Settings are grouped by purpose. Each group starts with an overview table.
Settings that are deprecated are listed last in their group.

.. conda-config-reference::
