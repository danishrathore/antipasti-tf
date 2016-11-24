from .. import pyutils as py
from ..layers import Layer
from ..models import Model


class LayerTrainyard(Model):
    """Class to implement arbitrary architectures."""
    def __init__(self, trainyard, input_shape=None, name=None):
        """

        :param trainyard:
        :param input_shape:
        """
        # TODO: Write doc
        # Initialze superclass
        super(LayerTrainyard, self).__init__(name=name)

        # Meta
        self._trainyard = None

        # Assign and parse trainyard
        self.trainyard = trainyard

        # Run shape inference
        self.input_shape = input_shape

    @property
    def trainyard(self):
        return self._trainyard

    @trainyard.setter
    def trainyard(self, value):
        # Remove singleton sublists
        value = py.removesingletonsublists(value)
        # Parse value. This is the magic Antipasti line.
        value = [[LayerTrainyard(elem_in_elem) if isinstance(elem_in_elem, list) else elem_in_elem
                  for elem_in_elem in elem]
                 if isinstance(elem, list) else elem for elem in value]
        self._trainyard = value

    @property
    def parameters(self):
        # Note that we don't use self._parameters defined in the superclass.
        return [parameter
                for train in self.trainyard
                for coach in py.obj2list(train)
                for parameter in coach.parameters]

    # Model.input_shape.setter must be overriden to handle e.g. multiple inputs.
    @Model.input_shape.setter
    def input_shape(self, value):
        if value is None:
            # Get input shape from trainyard
            if isinstance(self.trainyard[0], list):
                # Case: Multiple inputs to the trainyard
                _input_shape = [input_layer.input_shape for input_layer in self.trainyard[0]]
            else:
                # Case: Single input to the trainyard
                _input_shape = self.trainyard[0].input_shape
        else:
            # input shape is given.
            _input_shape = value
        # Run shape inference and set _output_shape
        output_shape = self.infer_output_shape(input_shape=_input_shape)
        # Set input and output shapes
        self._input_shape = _input_shape
        self._output_shape = output_shape

    def infer_output_shape(self, input_shape=None):
        if input_shape is None:
            input_shape = self.input_shape

        # Note that if the trainyard has multiple inputs, input_shape is a list of lists.
        intermediate_shape = input_shape
        # Trains and coaches are legacy terminology from the old theano Antipasti.
        # Loop over all layers or groups of layers (depth-wise)
        for train in self.trainyard:

            if isinstance(train, list):
                # If we're in here, it's because train is a group of width-wise stacked layers
                train_output_shape = []
                # Convert intermediate_shape to a list of lists
                train_input_shape = py.list2listoflists(intermediate_shape)
                # Cursor for keeping track (see below).
                cursor = 0

                # Loop over all layers (width-wise)
                for coach in train:
                    # This will save a function call
                    num_inputs_to_coach = coach.num_inputs
                    # coach can take more than one inputs, and cursor is to keep track of how many inputs have been \
                    # taken from train_input_shape.
                    coach_input_shape = py.delist(train_input_shape[cursor:cursor+num_inputs_to_coach])
                    cursor += num_inputs_to_coach

                    # Assign input shape to coach
                    coach.input_shape = coach_input_shape
                    # Get the resulting output shape and append to the list keeping track of train output shapes
                    train_output_shape.append(coach.output_shape)

            else:
                # If we're in here, it's because train is just a Layer (or a LayerTrainyard). Remember,
                # intermediate_shape can be a list of lists if train takes more than one inputs.
                train.input_shape = intermediate_shape
                train_output_shape = train.output_shape

            # Assign as intermediate shape
            intermediate_shape = py.delist(py.delistlistoflists(py.list2listoflists(train_output_shape)))

        # Done. final_shape = intermediate_shape, but we'll spare us the trouble
        return intermediate_shape

    # Parameter assignment cannot be handled by the superclass
    def assign_parameters(self, parameters=None):
        if parameters is not None:
            # TODO (See Layer.assign_parameters for potential pitfalls)
            pass

    # Feedforward, but without the decorator
    def feedforward(self, input=None):
        # Check if input is given
        if input is None:
            self.x = input
        else:
            input = self.x

        # If trainyard empty: nothing to do, return input
        if not self.trainyard:
            self.y = input
            return self.y

        # The input must be set for all input layers (if there are more than one)
        input_list = py.obj2list(input)
        # The individual input layers may have one or more inputs. The cursor is to keep track.
        cursor = 0

        # Loop over input layers (width-wise)
        for coach in py.obj2list(self.trainyard[0]):
            # Get number of inputs to the coach
            num_inputs_to_coach = coach.num_inputs
            # Fetch from list of inputs
            coach_input = py.delist(input_list[cursor:cursor+num_inputs_to_coach])
            # Increment cursor
            cursor += num_inputs_to_coach
            # Set input
            coach.x = coach_input

        # Feedforward recursively.
        intermediate_result = input
        for train in self.trainyard:
            if isinstance(train, list):
                # Convert intermediate_result to a list
                input_list = py.obj2list(intermediate_result)
                # Make a cursor to index input_list
                cursor = 0
                # List to store outputs from coaches in train
                coach_outputs = []

                for coach in train:
                    num_inputs_to_coach = coach.num_inputs
                    coach_input = py.delist(input_list[cursor:cursor+num_inputs_to_coach])
                    cursor += num_inputs_to_coach
                    # Feedforward and store output in list
                    coach_outputs.append(coach.feedforward(input=coach_input))
                intermediate_result = coach_outputs

            else:
                intermediate_result = train.feedforward(input=intermediate_result)

            # Flatten any recursive outputs to a linear list
            intermediate_result = py.delist(list(py.flatten(intermediate_result)))

        # The final intermediate_result is the final result (no shit sherlock)
        self.y = intermediate_result
        # Done.
        return self.y

    # Depth-wise mechanics
    def __add__(self, other):
        if self.num_outputs != other.num_inputs:
            raise RuntimeError(self._stamp_string("Cannot chain component with {} output(s) with "
                                                  "one with {} inputs.".format(self.num_outputs, other.num_inputs)))
        # Other could be a Layer or a LayerTrainyard
        if isinstance(other, Layer):
            return LayerTrainyard(self.trainyard + [other])
        elif isinstance(other, LayerTrainyard):
            return LayerTrainyard(self.trainyard + other.trainyard)
        else:
            raise TypeError(self._stamp_string("Second summand of invalid type. Expected Layer or LayerTrainyard, "
                                               "got '{}' instead.".format(other.__class__.__name__)))

    # Width-wise mechanics
    def __mul__(self, other):
        # Other could be a Layer or a LayerTrainyard
        if not (isinstance(other, Layer) or isinstance(other, LayerTrainyard)):
            raise TypeError(self._stamp_string("Second summand of invalid type. Expected Layer or LayerTrainyard, "
                                               "got '{}' instead.".format(other.__class__.__name__)))

        return LayerTrainyard([[self, other]])

    # Syntactic candy
    def __getitem__(self, item):
        pass