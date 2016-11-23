__author__ = "Nasim Rahaman"

import numpy as np
import tensorflow as tf

import pyutils as py


def forward_pass(forward_function):
    """Decorator for the feedforward method of `Layer`."""
    def _feedforward(cls, input=None):
        # Define behaviour for when input is None:
        if input is None:
            input = cls.x
        else:
            cls.x = input
        # Evaluate output
        output = forward_function(cls, input=input)
        # Assign output to y
        cls.y = output
        # Return output
        return output
    # Return decorated function
    return _feedforward


class Layer(object):
    """
    Abstract Layer class. This class implements basic layer mechanics (addition and multiplication) in addition to
    parameter value assignment.
    """
    def __init__(self, name=None):
        """
        Constructor for the Layer superclass.

        :type name: str
        :param name: Layer name (optional)
        """

        # "Private" variable for name
        self._name = None
        # Set name
        self.name = name

        # "Private" variables for input and output shapes
        self._input_shape = None
        self._output_shape = None

        # Container for parameters
        self._parameters = []

        # Containers for input and output
        self.x = None
        self.y = None

    @property
    def name(self):
        return str(id(self)) if self._name is None else self._name

    @name.setter
    def name(self, value):
        pass

    def _stamp_string(self, string):
        return "[LayerID:{}] {}".format(self.name, string)

    @property
    def input_shape(self):
        """
        Shape(s) of the layer input tensor(s). If more than one variable go in as inputs, `input_shape` is a list of
        their shapes, ergo a list of lists.

        :rtype list or list of list
        """
        return self._input_shape

    @input_shape.setter
    def input_shape(self, value):
        # Run shape inference
        output_shape = self.infer_output_shape(input_shape=value)
        # If no errors found, set to internal variables
        self._input_shape = value
        self._output_shape = output_shape

    @property
    def output_shape(self):
        """
        Shape(s) of the layer output tensor(s). If more than one variable come out as outputs, `output_shape` is a list
        of their shapes, ergo a list of lists.

        :rtype list or list of list
        """
        return self._output_shape

    @property
    def num_inputs(self):
        """
        Number of inputs to the layer.

        :rtype: int
        """
        # Observe that num_inputs = 1 when self.input_shape = None (legacy behaviour)
        return 1 if py.islistoflists(self.input_shape) else len(self.input_shape)

    @property
    def num_outputs(self):
        """
        Number of outputs from the layer.

        :rtype: int
        """
        # Observe that num_outputs = 1 when self.input_shape = None (legacy behaviour)
        return 1 if py.islistoflists(self.output_shape) else len(self.output_shape)

    @property
    def input_dimensions(self):
        """
        Dimensions of the input tensor(s), i.e. `len(input.shape)`.
        If more than one input go in to the layer, `input_dimensions` is a list of input dimensions.

        :rtype: int or list of int
        """
        # Defined only if input_shape is defined.
        if self.input_shape is None:
            raise ValueError(self._stamp_string("Input shape is not known. Set Layer.input_shape first."))
        # Legacy helpers to the rescue!
        return py.delist([len(ishp) for ishp in py.list2listoflists(self.input_shape)])

    @property
    def output_dimensions(self):
        """
        Dimensions of the output tensor(s), i.e. `len(output.shape)`.
        If more than one output comes out from the layer, `output_dimensions` is a list of output dimensions.

        :rtype: int or list of int
        """
        # Defined only if output_shape is defined, which is in turn defined only if input_shape is defined.
        if self.output_shape is None:
            raise ValueError(self._stamp_string("Output shape could not be inferred. Set Layer.input_shape first."))

        return py.delist([len(oshp) for oshp in py.list2listoflists(self.output_shape)])

    @property
    def parameters(self):
        """Parameters (e.g. Weights, Biases, etc.) of the layer."""
        return self._parameters

    @parameters.setter
    def parameters(self, value):
        self.assign_parameters(parameters=value)

    def infer_output_shape(self, input_shape=None, validate=True):
        """
        Infer output shape for given `input_shape`. If `validate` is set to true, the `input_shape` will be checked
        for consistency.

        :type input_shape: list or list of list
        :param input_shape: Shape of the layer input(s), as a list (1 input) or a list of lists (multiple inputs).

        :type validate: bool
        :param validate: Whether to validate `input_shape`.
        """
        # This boils down to the default behaviour being to set output_shape = input_shape.
        if input_shape is None:
            input_shape = self.input_shape
        return input_shape

    @forward_pass
    def feedforward(self, input=None):
        """
        Implements the forward pass for the layer, given its input. If the decorator forward_pass is not used, this
        method should read its input from `Layer.x` (if necessary) and write its output to `Layer.y`.
        """
        return input

    def assign_parameters(self, parameters=None, validate=True):
        """
        Given a list of parameters (numpy arrays or tf.Variable), validate if possible/requested and assign them as
        layer parameters.

        :type parameters: list
        :param parameters: List of parameters (as numpy array or tf.Variable).

        :type validate: bool
        :param validate: Whether to validate parameter shapes (if possible).
        """
        if parameters is not None:
            # TODO Parameter assignment with tf.assign
            pass

    def __add__(self, other):
        """
        Stack depth-wise.

        :type other: Layer or LayerTrainYard
        :param other: The other `Layer` or `LayerTrainYard`.
        """
        # TODO Can be done once LayerTrainYard is defined.
        pass

    def __mul__(self, other):
        """
        Stack width-wise.

        :type other: Layer or LayerTrainYard
        :param other: The other `Layer` or `LayerTrainYard`.
        """
        # TODO Can be done once LayerTrainYard is defined.
        pass