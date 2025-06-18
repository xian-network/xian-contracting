from types import ModuleType
import nacl

# ============================================================================
# SIMPLE COST TRACKING (No Mocks, No Abstractions)
# ============================================================================

def _add_cost(amount: int):
    """
    Simple cost tracking - directly access runtime if available.
    No mocks, no abstractions, just direct access with safe fallbacks.
    """
    try:
        # Try to import and use runtime directly
        from contracting.execution import runtime
        if hasattr(runtime, 'rt') and runtime.rt is not None:
            if hasattr(runtime.rt, 'tracer') and runtime.rt.tracer is not None:
                # Check if tracer is actually started (not a mock)
                if hasattr(runtime.rt.tracer, 'add_cost') and callable(runtime.rt.tracer.add_cost):
                    # Only add cost if tracer is properly initialized
                    if hasattr(runtime.rt.tracer, 'is_started'):
                        if runtime.rt.tracer.is_started():
                            runtime.rt.tracer.add_cost(amount)
                    else:
                        # If no is_started method, assume it's active and add cost
                        runtime.rt.tracer.add_cost(amount)
    except (ImportError, AttributeError, TypeError):
        # Silently fail if runtime is not available or improperly set up
        # This handles test environments and other edge cases gracefully
        pass

# ============================================================================
# CRYPTO FUNCTIONS (Now Isolated from Runtime)
# ============================================================================

def verify(vk: str, msg: str, signature: str):
    """Verify a signature using NaCl - no cost tracking needed for existing function"""
    vk = bytes.fromhex(vk)
    msg = msg.encode()
    signature = bytes.fromhex(signature)

    vk = nacl.signing.VerifyKey(vk)
    try:
        vk.verify(msg, signature)
    except:
        return False
    return True


def key_is_valid(key: str):
    """Check if the given address is valid - no cost tracking needed for existing function"""
    if not len(key) == 64:
        return False
    try:
        int(key, 16)
    except:
        return False
    return True


def ecdsa_verify(public_key: str, message: str, signature: str, curve: str = 'secp256k1') -> bool:
    """
    Verify an ECDSA signature using the ecdsa library.
    Costs 3 stamps base cost + 1 stamp per KB of message size.
    
    Args:
        public_key: Hex-encoded public key (uncompressed format or compressed)
        message: Message that was signed (string, max 10KB)
        signature: Hex-encoded signature (DER format)
        curve: Curve name ('secp256k1', 'secp256r1', 'secp384r1', 'secp521r1')
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    # Restrict message size to prevent abuse (10KB limit)
    assert len(message) <= 10240, f"Message size {len(message)} bytes exceeds maximum limit of 10,240 bytes (10KB)"
    
    # Calculate cost: 3 stamps base + 1 stamp per KB (rounded up)
    message_size_kb = (len(message) + 1023) // 1024  # Round up to nearest KB
    total_cost = 3 + message_size_kb  # Base 3 stamps + size-based cost
    
    # Isolated cost tracking - no runtime knowledge required
    _add_cost(total_cost * 1000)  # Convert to internal units (stamps * 1000)
    
    try:
        from ecdsa import VerifyingKey, SECP256k1, NIST256p, NIST384p, NIST521p
        from ecdsa.util import sigdecode_der
        import hashlib
        
        # Map curve names to ecdsa curve objects
        curve_map = {
            'secp256k1': SECP256k1,
            'secp256r1': NIST256p,
            'secp384r1': NIST384p,
            'secp521r1': NIST521p
        }
        
        if curve not in curve_map:
            return False
        
        ecdsa_curve = curve_map[curve]
        
        # Decode public key from hex
        public_key_bytes = bytes.fromhex(public_key)
        
        # Handle both compressed and uncompressed public key formats
        if len(public_key_bytes) == ecdsa_curve.verifying_key_length:
            # Uncompressed format (without 0x04 prefix)
            vk = VerifyingKey.from_string(public_key_bytes, curve=ecdsa_curve)
        elif len(public_key_bytes) == ecdsa_curve.verifying_key_length + 1 and public_key_bytes[0] == 0x04:
            # Uncompressed format (with 0x04 prefix)
            vk = VerifyingKey.from_string(public_key_bytes[1:], curve=ecdsa_curve)
        else:
            # Try compressed format or other formats
            vk = VerifyingKey.from_string(public_key_bytes, curve=ecdsa_curve)
        
        # Decode signature from hex
        signature_bytes = bytes.fromhex(signature)
        
        # Encode message to bytes
        message_bytes = message.encode('utf-8')
        
        # Verify signature using SHA256 hash and DER encoding
        return vk.verify(signature_bytes, message_bytes, hashlib.sha256, sigdecode_der)
        
    except Exception:
        return False

# ============================================================================
# MODULE EXPORTS (Simple and Clean)
# ============================================================================



crypto_module = ModuleType('crypto')
crypto_module.verify = verify
crypto_module.key_is_valid = key_is_valid
crypto_module.ecdsa_verify = ecdsa_verify

exports = {
    'crypto': crypto_module
}
