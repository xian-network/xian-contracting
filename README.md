# Xian Contracting

Xian Contracting is a Python-based smart contract development and execution framework. Unlike traditional blockchain platforms like Ethereum, Xian Contracting leverages Python's VM to create a more accessible and familiar environment for developers to write smart contracts.

## Features

- **Python-Native**: Write smart contracts in standard Python with some additional decorators and constructs
- **Storage System**: Built-in ORM-like system with `Variable` and `Hash` data structures
- **Runtime Security**: Secure execution environment with memory and computation limitations
- **Metering System**: Built-in computation metering to prevent infinite loops and resource abuse
- **Event System**: Built-in logging and event system for contract state changes
- **Import Controls**: Secure import system that prevents access to dangerous system modules

## Installation

```bash
pip install xian-contracting
```

## Quick Start

Here's a complete token contract example with approval system:

```python
def token_contract():
    balances = Hash()
    owner = Variable()
    
    @construct
    def seed():
       owner.set(ctx.caller)
    
    @export
    def approve(amount: float, to: str):
       assert amount > 0, 'Cannot send negative balances.'
       balances[ctx.caller, to] += amount
    
    @export
    def transfer_from(amount: float, to: str, main_account: str):
        approved = allowances[main_account, ctx.caller]
    
        assert amount > 0, 'Cannot send negative balances!'
        assert approved >= amount, f'You approved {approved} but need {amount}'
        assert balances[main_account] >= amount, 'Not enough tokens to send!'
    
        allowances[main_account, ctx.caller] -= amount
        balances[main_account] -= amount
        balances[to] += amount
    
    @export
    def transfer(amount: float, to: str):
       assert amount > 0, 'Cannot send negative balances.'
       assert balances[ctx.caller] >= amount, 'Not enough coins to send.'
    
       balances[ctx.caller] -= amount
       balances[to] += amount
    
    @export
    def mint(to, amount):
       assert ctx.caller == owner.get(), 'Only the original contract author can mint!'
       balances[to] += amount
```

## Core Concepts

### Storage Types

- **Variable**: Single-value storage
  ```python
  counter = Variable()
  counter.set(0)  # Set value
  current = counter.get()  # Get value
  ```

- **Hash**: Key-value storage with support for complex and multi-level keys
  ```python
  balances = Hash()
  # Single-level key
  balances['alice'] = 100
  alice_balance = balances['alice']
  
  # Multi-level keys for complex relationships
  balances['alice', 'bob'] = 50  # e.g., alice approves bob to spend 50 tokens
  approved_amount = balances['alice', 'bob']  # Get the approved amount
  
  # You can use up to 16 dimensions in key tuples
  data['user', 'preferences', 'theme'] = 'dark'
  ```

### Contract Decorators

- **@construct**: Initializes contract state (can only be called once)
  ```python
  @construct
  def seed():
      owner.set(ctx.caller)
  ```

- **@export**: Makes function callable from outside the contract
  ```python
  @export
  def increment(amount: int):
      counter.set(counter.get() + amount)
  ```

### Contract Context

The `ctx` object provides important runtime information:

- `ctx.caller`: Address of the account calling the contract
- `ctx.this`: Current contract's address
- `ctx.signer`: Original transaction signer
- `ctx.owner`: Contract owner's address

## Using the ContractingClient

The `ContractingClient` class is your main interface for deploying and interacting with contracts:

```python
from contracting.client import ContractingClient

# Initialize the client
client = ContractingClient()

# Submit a contract
with open('token.py', 'r') as f:
    contract = f.read()
    
client.submit(name='con_token', code=contract)

# Get contract instance
token = client.get_contract('con_token')

# Call contract methods
token.transfer(amount=100, to='bob')
```

## Storage Driver

The framework includes a powerful storage system:

```python
from contracting.storage.driver import Driver

driver = Driver()

# Direct storage operations
driver.set('key', 'value')
driver.get('key')

# Contract storage
driver.set_contract(name='contract_name', code=contract_code)
driver.get_contract('contract_name')
```

## Event System

Contracts can emit events which can be tracked by external systems:

```python
def token_contract():
    transfer_event = LogEvent(
        'transfer',
        {
            'sender': {'type': str, 'idx': True},
            'receiver': {'type': str, 'idx': True},
            'amount': {'type': float}
        }
    )

    @export
    def transfer(amount: float, to: str):
        # ... transfer logic ...
        
        # Emit event
        transfer_event({
            'sender': ctx.caller,
            'receiver': to,
            'amount': amount
        })
```

## Security Features

- Restricted imports to prevent malicious code execution
- Memory usage tracking and limitations
- Computation metering to prevent infinite loops
- Secure runtime environment
- Type checking and validation
- Private method protection

## Development and Testing

When developing contracts, you can use the linter to check for common issues:

```python
from contracting.client import ContractingClient

client = ContractingClient()
violations = client.lint(contract_code)
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
