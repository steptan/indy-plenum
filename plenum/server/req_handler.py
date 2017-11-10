from abc import ABCMeta, abstractmethod
from typing import List

import base58

from common.serializers.serialization import proof_nodes_serializer, state_roots_serializer
from plenum.bls.bls_store import BlsStore
from plenum.common.constants import DATA, STATE_PROOF, TXN_TIME, ROOT_HASH, MULTI_SIGNATURE, PROOF_NODES
from plenum.common.ledger import Ledger
from plenum.common.plenum_protocol_version import PlenumProtocolVersion
from plenum.common.request import Request
from plenum.common.types import f
from plenum.persistence.util import txnsWithSeqNo
from state.pruning_state import PruningState
from stp_core.common.log import getlogger

logger = getlogger()


class RequestHandler(metaclass=ABCMeta):
    """
    Base class for request handlers
    Declares methods for validation, application of requests and
    state control
    """

    def __init__(self, ledger: Ledger, state: PruningState, bls_store: BlsStore):
        self.ledger = ledger
        self.state = state
        self.bls_store = bls_store

    @abstractmethod
    def validate(self, req: Request, config=None):
        """
        Validates request. Raises exception if request is invalid.
        """

    @abstractmethod
    def apply(self, req: Request, cons_time: int):
        """
        Applies request
        """

    @abstractmethod
    def updateState(self, txns, isCommitted=False):
        """
        Updates current state with a number of committed or
        not committed transactions
        """

    def commit(self, txnCount, stateRoot, txnRoot) -> List:
        """
        :param txnCount: The number of requests to commit (The actual requests are
        picked up from the uncommitted list from the ledger)
        :param stateRoot: The state trie root after the txns are committed
        :param txnRoot: The txn merkle root after the txns are committed

        :return: list of committed transactions
        """

        (seqNoStart, seqNoEnd), committedTxns = \
            self.ledger.commitTxns(txnCount)
        stateRoot = base58.b58decode(stateRoot.encode())
        # Probably the following assertion fail should trigger catchup
        assert self.ledger.root_hash == txnRoot, '{} {}'.format(
            self.ledger.root_hash, txnRoot)
        self.state.commit(rootHash=stateRoot)
        return txnsWithSeqNo(seqNoStart, seqNoEnd, committedTxns)

    def onBatchCreated(self, stateRoot):
        pass

    def onBatchRejected(self):
        pass

    @abstractmethod
    def get_path_for_txn(self, txn):
        pass

    def make_proof(self, path):
        '''
        Creates a state proof for the given path in state trie.
        Returns None if there is no BLS multi-signature for the given state (it can
        be the case for txns added before multi-signature support).

        :param path: the path generate a state proof for
        :return: a state proof or None
        '''
        if self.bls_store is None:
            # we may not have it for pool ledger
            return None

        proof = self.state.generate_state_proof(path, serialize=True)
        root_hash = self.state.committedHeadHash
        encoded_proof = proof_nodes_serializer.serialize(proof)
        encoded_root_hash = state_roots_serializer.serialize(bytes(root_hash))

        multi_sig = self.bls_store.get(encoded_root_hash)
        if not multi_sig:
            return None

        return {
            ROOT_HASH: encoded_root_hash,
            MULTI_SIGNATURE: multi_sig.as_dict(),
            PROOF_NODES: encoded_proof
        }

    def make_write_result(self, request, txn, proof):
        result = txn

        if proof and request and request.protocolVersion and \
                        request.protocolVersion >= PlenumProtocolVersion.STATE_PROOF_SUPPORT.value:
            result[STATE_PROOF] = proof

        # Do not inline please, it makes debugging easier
        return result

    @staticmethod
    def make_read_result(request, data, last_seq_no, update_time, proof):
        result = {**request.operation, **{
            DATA: data,
            f.IDENTIFIER.nm: request.identifier,
            f.REQ_ID.nm: request.reqId,
            f.SEQ_NO.nm: last_seq_no,
            TXN_TIME: update_time
        }}
        if proof and request.protocolVersion and \
                        request.protocolVersion >= PlenumProtocolVersion.STATE_PROOF_SUPPORT.value:
            result[STATE_PROOF] = proof

        # Do not inline please, it makes debugging easier
        return result
