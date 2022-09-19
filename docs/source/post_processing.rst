Post Processing with Pyrefine
-----------------------------

Pyrefine has the ability to post-process a series of simulations over a mesh adaptation and extract quantities of interest for each mesh.
There are premade scripts available or a custom post-processor can be created to manipulate the raw data that is read from the history files.


Scripts
--------

FUN3D Steady History to tecplot - pr_post_fun3d_steady_hist_to_tec.py
=====================================================================
.. argparse::
    :ref: pyrefine.post_processing.pr_post_fun3d_steady_hist_to_tec.arg_parser
    :prog: pr_post_fun3d_steady_hist_to_tec

Customizing the Post-Processor
------------------------------

The post processing class, :class:`~pyrefine.post_processing.fun3d_file_reader.Fun3dAdaptationSteadyHistoryReader`, is meant to be flexible.
Arbitrary commands can be added to the post processor without modifying the source code for the reader class.
This is possible through the use of the Command design pattern.
Post-processing steps are encapsulated as "command" objects.
These commands are added to the reader class through the :meth:`~pyrefine.post_processing.fun3d_file_reader.Fun3dAdaptationSteadyHistoryReader.register_command` method.
The commands are stored in a list and can be run in order.

Each command should be a class that overrides the abstract base class, :class:`~pyrefine.post_processing.post_processing_command.PostProcessingCommand`.
Each child class must implement the method :meth:`~pyrefine.post_processing.post_processing_command.PostProcessingCommand.execute`.
This method is meant to contain the bulk of the post-processing work.
When the :meth:`~pyrefine.post_processing.fun3d_file_reader.Fun3dAdaptationSteadyHistoryReader.execute_commands` method is called,
it will call the `execute` method on each command sequentially.

In this implementation of the command design pattern, the roles are set up as follows:

- Invoker or Dispatcher: :class:`~pyrefine.post_processing.fun3d_file_reader.Fun3dAdaptationSteadyHistoryReader`
- Abstract base class for commands: :class:`~pyrefine.post_processing.post_processing_command.PostProcessingCommand`
- Concrete commands: User-defined
- Receiver: User-defined.  In order to modify :class:`~pyrefine.post_processing.fun3d_file_reader.Fun3dAdaptationSteadyHistoryReader` as part of post-processing,
  the reader object should be setup as the invoker and the receiver.

Example
-------

.. code-block:: python

    from pyrefine.post_processing.fun3d_file_reader import Fun3dAdaptationSteadyHistoryReader as F3DReader
    from pyrefine.post_processing.post_processing_command import PostProcessingCommand

    class LOverDCommand(PostProcessingCommand):
        """
        A command to compute the lift-to-drag ratio using the existing values
        of `C_L` and `C_D`
        """
        def execute(self):
            """ Override method from abstract base class"""
            c_l = self.target.final_hist_values['C_L']
            c_d = self.target.final_hist_values['C_D']
            self.target.final_hist_values['L/D'] = c_l / c_d

    # Setup the reader class
    reader = F3DReader('folder', 'project')
    new_command = LOverDCommand(reader)
    reader.register_command(new_command)
    reader.execute_commands()
    print(reader.final_hist_values['L/D'])

Reader Class
------------

.. automodule:: pyrefine.post_processing.fun3d_file_reader

.. autoclass:: Fun3dAdaptationSteadyHistoryReader
   :members:


PostProcessCommand Class
------------------------
.. automodule:: pyrefine.post_processing.post_processing_command

.. autoclass:: PostProcessingCommand
   :members:
