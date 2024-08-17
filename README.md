# Contracting - Smart Contracts in Python

Contracting is a smart contracting library. Unlike Bitcoin and Ethereum, Contracting leverages the existing PythonVM to create a system that allows developers to write small applications for the  types of logic we see in smart contracts today. This generally has to do with simple logical transactions. Contracting focuses on making standard CRUD operations extremely easy with full support for JSON objects and dynamic storage sizing so you spend less time with lower level computer science details and more time coding.

### Example
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
         assert amount > 0, 'Cannot send negative balances.'
         assert balances[main_account, ctx.caller] >= amount, f'Not enough coins approved to send. You have {balances[main_account, ctx.caller]} and are trying to spend {amount}'
         assert balances[main_account] >= amount, 'Not enough coins to send.'
     
         balances[main_account, ctx.caller] -= amount
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

### Installing

`pip install -e .`



### Docs & More
Official docs and walkthrough are available at https://github.com/xian-network/smart-contracts-docs

