import base64
import json

from typing import Protocol, Dict, TypeVar, Generic, List, get_args

# Constants
class ConnectionConstants:
    wire_ball_attachment1: int = 1
    wire_ball_attachment2: int = 3

    label_cup: int = 1

    connector_bottom_attachment: int = 5
    connector_top_cup: int = 4
    connector_front_cup: int = 6
    connector_back_cup: int = 3
    connector_side_cup1: int = 2
    connector_side_cup2: int = 1

    gate_attachment: int = 4
    tri_gate_output: int = 1
    tri_gate_input1: int = 2
    tri_gate_input2: int = 3

    two_gate_output: int = 1
    two_gate_input: int = 2

    wire_cup1: int = 4
    wire_cup2: int = 2

# Classes
class HasCups(Protocol):
    cups: Dict[int, bool]

class CompileStack:
    def __init__(self):
        self._stack = []
        self._items = []
    
    def append(self, stackItem, classItem):
        self._stack.append(stackItem)
        self._items.append(classItem)
        return len(self._stack)
    
    def terminate(self):
        encoded = base64.b64encode(json.dumps(self._stack).encode('utf-8'))
        return encoded

class BaseItem:
    Attachments = {}
    Cups = {}
    Name = ""

    def __init__(self):
        self._id = -1
        self._compiled = False
        self.attachments = self.Attachments.copy()
        self.cups = self.Cups.copy()
        self._positions = []

    def _getEmptyAttachment(self):
        foundId = -1

        for attachmentId, used in self.attachments.items():
            if used == False:
                foundId = attachmentId
                break

        return foundId

    def connect(self, element: HasCups, cup):
        if element.cups[cup] == True:
            raise Exception("Cup is already used !")
        attachment = self._getEmptyAttachment()

        if attachment == -1:
            raise Exception("No found empty attachment !")

        self.attachments[attachment] = True
        element.cups[cup] = True

        if element._id != -1:
            element = element._id

        self._positions.append([attachment, cup, element])
    
    def compile(self, stack: CompileStack):
        item = [self.Name]
        self._compiled = True

        for position in self._positions:
            if isinstance(position[2], int):
                continue
            
            if position[2]._id == -1:
                raise Exception("All connections are not compiled !")
            
            position[2] = position[2]._id
        
        item.append(self._positions)
        item.append([])

        id = stack.append(item, self)
        self._id = id

# Gates
class GateAND(BaseItem):
    Attachments = {
        ConnectionConstants.gate_attachment: False
    }
    Cups = {
        ConnectionConstants.tri_gate_output: False,
        ConnectionConstants.tri_gate_input1: False,
        ConnectionConstants.tri_gate_input2: False
    }
    Name = "Gate-AND"

class GateOR(BaseItem):
    Attachments = {
        ConnectionConstants.gate_attachment: False
    }
    Cups = {
        ConnectionConstants.tri_gate_output: False,
        ConnectionConstants.tri_gate_input1: False,
        ConnectionConstants.tri_gate_input2: False
    }
    Name = "Gate-OR"
    
class GateNOT(BaseItem):
    Attachments = {
        ConnectionConstants.gate_attachment: False
    }
    Cups = {
        ConnectionConstants.two_gate_output: False,
        ConnectionConstants.two_gate_input: False,
    }
    Name = "Gate-NOT"

# Base parts
class Connector(BaseItem):
    Attachments = {
        ConnectionConstants.connector_bottom_attachment: False
    }
    Cups = {
        ConnectionConstants.connector_top_cup: False,
        ConnectionConstants.connector_front_cup: False,
        ConnectionConstants.connector_back_cup: False,
        ConnectionConstants.connector_side_cup1: False,
        ConnectionConstants.connector_side_cup2: False
    }
    Name = "Connector"

class Label(BaseItem):
    Cups = {
        ConnectionConstants.label_cup: False,
    }
    Name = "InputSensor"

    def __init__(self, text: str):
        super().__init__()
        self._str = text

    def compile(self, stack: CompileStack):
        item = [self.Name,[],{"ActivationKey":self._str}]
        self._compiled = True
        
        id = stack.append(item, self)
        self._id = id

# Wire types
class Wire(BaseItem):
    Attachments = {
        ConnectionConstants.wire_ball_attachment1: False,
        ConnectionConstants.wire_ball_attachment2: False
    }
    Cups = {
        ConnectionConstants.wire_cup1: False,
        ConnectionConstants.wire_cup2: False,
    }
    Name = "Wire"

class Switch(Wire):
    Attachments = {
        ConnectionConstants.wire_ball_attachment2: False,
        ConnectionConstants.wire_ball_attachment1: False
    }
    Cups = {
        ConnectionConstants.wire_cup2: False,
    }
    Name = "Switch"

# Stackable wire types
A = TypeVar('A', bound='Wire')
B = TypeVar('B', bound='Wire')

class StackableWireType(BaseItem, Generic[A, B]):
    _item_cls: type
    _base_cls: type

    def __init_subclass__(cls):
        super().__init_subclass__()

        generic_args = get_args(cls.__orig_bases__[0])
        cls._item_cls = generic_args[0]
        cls._base_cls = generic_args[1]

    def __init__(self):
        super().__init__()

        self.cups = self._item_cls.Cups.copy()
        self.attachments = self._item_cls.Attachments.copy()
        self.name = self._base_cls.Name

        self._items: List[A] = [self._base_cls()]

    def _getLatestItem(self) -> A:
        last_item = self._items[-1]
        for item in self._items:
            free_attachments = [k for k, v in item.attachments.items() if not v]
            if free_attachments:
                return item

        free_cups = [k for k, v in last_item.cups.items() if not v]
        new_item = self._item_cls()
        new_item.connect(last_item, free_cups[0])
        self._items.append(new_item)
        return new_item

    @property
    def _id(self):
        possible_ids = []
        for item in self._items:
            if item._id == -1:
                continue
            possible_ids.append([item._id, len([k for k, v in item.cups.items() if not v])])
        if not possible_ids:
            return -1
        return max(possible_ids, key=lambda x: x[1])[0]

    @_id.setter
    def _id(self, value):
        pass
    
    def connect(self, element: 'HasCups', cup):
        latest_item = self._getLatestItem()
        latest_item.connect(element=element, cup=cup)

    def compile(self, stack: 'CompileStack'):
        self._compiled = True
        for item in self._items:
            item.compile(stack=stack)

class StackableWire(StackableWireType[Wire, Wire]):
    def __init__(self):
        super().__init__()

class StackableSwitch(StackableWireType[Wire, Switch]):
    def __init__(self):
        super().__init__()