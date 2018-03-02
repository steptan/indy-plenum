from plenum.test.test_node import TNode


def getProtocolInstanceNums(node: TNode):
    return [node.instances.masterId, *node.instances.backupIds]
