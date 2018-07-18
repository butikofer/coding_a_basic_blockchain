#!/usr/bin/env python3.7

# MIT License
# Copyright (c) 2018 Josh Butikofer
# See accompanying LICENSE file for license information.

# This code demonstrates some of the basic technologies of "blockchain" and how they work together. I try to
# show how a blockchain (or distributed ledger) uses technology from cryptography like hashing and public-key signatures
# to ensure immutability and auditability. This code also implements one of the basic proof-of-work decentralized
# consensus algorithms. There is obviously a lot missing from the below code that exists in a fully-built blockchain
# implementation, but of note is a lack of networking code to connect blockchain nodes together and a "tie breaker"
# algorithm for those nodes to negotiate which miner wins when more than one mines a block.

# We will be using some of the niceties of Python 3.7 and a helpful crypto library to help with public-key signing
from dataclasses import dataclass, field
from typing import *
import rsa # Don't implement your own
import hashlib
import time

@dataclass  # New Python 3.7 feature!
class Transaction:
    sender_address: rsa.PublicKey
    recipient_address: rsa.PublicKey
    value: float
    signature: bytes = field(default=None)
       
    def sign(self, sender_private_key):
        """Takes a private key, which the sender should never share, and signs this transaction to verify
        they want to transfer the tokens. We sign the core attributes of the transaction using the private
        key. We will use SHA-256 as the signature hashing algorithm."""  
        self.signature = rsa.sign(self.get_core_data(), sender_private_key, 'SHA-256')
        self.validate()
        
    def get_core_data(self):
        """Provides the core info needed to sign the transaction--basically everything BUT the
        signature."""
        return (str(self.sender_address) + str(self.recipient_address) + str(self.value)).encode()
        
    def validate(self):
        """Validates the integrity of this transaction by using RSA to verify it is signed properly.
        Gets the core data about the transaction, and the signature made using the private key,
        and uses the public key to validate it is signed. The public key is the sender_address."""
        rsa.verify(self.get_core_data(), self.signature, self.sender_address)

@dataclass
class Block:
    num: int
    timestamp: int
    prev_block_hash: str
    transactions: List[Transaction]
    block_hash: str = field(default="")
    nonce: int = field(default=0)
      
    def hash(self) -> str:
        """Uses SHA-256 to hash the header of the block (the core attributes of the block).
        Saves the hash to the block object for later use and also returns the hash in hex format."""
        
        self.block_hash = hashlib.sha256(self.get_header()).hexdigest()
        return self.block_hash
    
    def get_header(self) -> bytes:
        """Returns a string that represents the core attributes that uniquely identify the block AND link
        it to the previous block (forming the chain). These attributes include: block num, timestamp,
        previous block hash, transactions (real chains use a Merkle root hash for efficiency), and a nonce."""
        
        return (str(self.num) + str(self.timestamp) + str(self.prev_block_hash) + str(self.nonce) + str(self.transactions)).encode()
    
    def validate(self, proof_of_work_func) -> bool:
        """Using the given function, ensure that this block hashes correctly, adhering to the agreed-upon
        consensus algorithm."""
        
        return proof_of_work_func(self.hash())


REWARD_AMOUNT = 2.0

class BlockchainNode:    
    
    def __init__(self, miner_address):
        self.miner_address: rsa.PublicKey = miner_address
        self.blocks: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.proof_of_work_func = lambda x: x.endswith('000')
        
        self.mine_block()
      
    def submit_transaction(self, transaction):        
        """This is used to submit a new transaction to the chain. End-users send transactions and aren't
        concerned about the blocks, per se. This function takes a signed transaction will validate it is
        cryptographically sound. It will then need to check that there is sufficient balance to make the
        transfer. If these are good, we will add the transaction to a list of those that will be considered
        when the next block is mined."""
        
        # Ensure the transaction is properly signed by the private key
        transaction.validate()
        
        # Make sure the funds exist for the requested transaction 

        sender_balance = self.get_balance(transaction.sender_address)
        
        if sender_balance < transaction.value:
            raise Exception(f"Insufficient tokens available ({transaction.value} required, {sender_balance} available)")
     
        # Transaction checks out--add to the list of our pending transactions!
        self.pending_transactions.append(transaction)
        
    def mine_block(self):
        """This function bundles all pending transactions and mines a new block. Mining is the process
        by which a node creates a new block. This is where the decentralized consensus algorithm comes in.
        We will be using a proof-of-work algorithm that is computationally expensive. This prevents bad actor
        nodes from flooding the P2P network with invalid transactions, blocks, or chains. It is too expensive to
        rewrite history, making the blockchain more secure from these kinds of attacks. This function will mine
        the new block and then append it to the chain automatically.
        
        Nodes that successfully mine a new block get a token award. This is how new tokens show up in the chain
        and this is supposed to incentivize more peers on the network.
        """
        
        # Make sure we have a genesis block to start the chain
        if len(self.blocks) <= 0:
            prev_hash = "-"
            next_num = 0
        else:
            prev_block = self.blocks[-1]
            prev_hash = prev_block.block_hash
            next_num = prev_block.num + 1
            
        new_block = Block(next_num, time.time(), prev_hash, self.pending_transactions.copy())

        # Add a reward transaction at the end of the block for this node
        
        reward = Transaction(None, self.miner_address, REWARD_AMOUNT)
        new_block.transactions.append(reward)
        
        # Execute proof-of-work
        self.execute_pow(new_block)
        
        # Add the block to the chain
        self.blocks.append(new_block)
        
        # Reset our pending transactions
        self.pending_transactions.clear()
                
        # Print out success
        print(f"Successfully mined new block {new_block.num}!")
        
        
    def execute_pow(self, block):
        """Using the defined proof-of-work lambda, increment the nonce on the block until
        we satisfy the lambda's assertion. Since this iterating and hashing can take a long
        time and a lot of CPU, it can become computationally intensive. When this function returns
        the block will have a nonce and hash that meet the consensus algorithm requirements and can
        be very easily checked."""
        block.nonce = 0
        while not block.validate(self.proof_of_work_func):
            block.nonce += 1
            
        print(f"Successfully found POW for block {block.num} with nonce {block.nonce}!")
        
    def validate_chain(self):
        """Verifies that this chain is cryptographically sound and has not been modified. Also ensures
        that all blocks meet the conensus algorithm requirements. This function is MUCH faster than mining
        new blocks: this is why the proof-of-work algorithm works well. Verification is very fast, but mining new
        blocks is difficult."""
        
        # Cycle through each block and compare previous block hashes and verify proof-of-work compliance.
        prev_hash = "-"
        for b in self.blocks:
            if b.prev_block_hash != prev_hash:
                raise Exception("Previous hashes do not match!")
            elif not b.validate(self.proof_of_work_func):
                raise Exception(f"Something is wrong with block hash {b.num}!")
                
            prev_hash = b.block_hash
                
        print(f"Successfully validated chain of size {len(self.blocks)}!")
        
    def get_balance(self, address):
        """This method provides an easy way to traverse the chain to find out the balance of the given address.
        Bitcoin doesn't necessarily work this way, but other chains do, and it works fine for our purposes. This
        method will return the token balance of the given address, returning 0.0 if the address has never been
        seen on the chain before."""
        
        balance = 0
        for b in self.blocks:
            for t in b.transactions:
                if t.sender_address == address:
                    balance -= t.value
                elif t.recipient_address == address:
                    balance += t.value
                    
        return balance


# Basic usage
if __name__ == "__main__":
    # First we need to generate some keys that we can use. Any RSA compatible keys should work with this code. For example, you could load them from
    # files or generate them from code.

    # Code generation
    public_key, private_key = rsa.newkeys(512)
    receiving_public_key, receiving_private_key = rsa.newkeys(512)

    # Reading from files examples:
    # Generating public/private keys via files
    # openssl genpkey -algorithm RSA -out blockchain.pem -pkeyopt rsa_keygen_bits:512
    # openssl rsa -pubout -RSAPublicKey_out -in blockchain.pem -out rsa_blockchain.pub
    # openssl rsa -in blockchain.pem -outform PEM -out rsa_blockchain

    # with open("rsa_blockchain") as f:
    #    private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
    #
    # with open("rsa_blockchain.pub") as f:
    #    public_key = rsa.PublicKey.load_pkcs1(f.read().encode())

    node = BlockchainNode(public_key)
    t1 = Transaction(public_key, receiving_public_key, 0.5)
    t1.sign(private_key)
    node.submit_transaction(t1)
    node.mine_block()

    t2 = Transaction(public_key, receiving_public_key, 1.0)
    t2.sign(private_key)
    node.submit_transaction(t2)
    node.mine_block()

    print(node.get_balance(public_key))
    print(node.get_balance(receiving_public_key))

    node.validate_chain()
