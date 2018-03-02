from plenum.common.messages.node_messages import Propagate
from plenum.test.spy_helpers import getAllArgs
from plenum.test.test_node import TNode


def sentPropagate(node: TNode):
    params = getAllArgs(node, TNode.send)
    return [p for p in params if isinstance(p['msg'], Propagate)]


def recvdPropagate(node: TNode):
    return getAllArgs(node,
                      TNode.processPropagate)


def recvdRequest(node: TNode):
    return getAllArgs(node,
                      TNode.processRequest)


def forwardedRequest(node: TNode):
    return getAllArgs(node,
                      TNode.forward)
