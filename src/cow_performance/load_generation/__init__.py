"""
Load generation module for CoW Protocol performance testing.

This module provides order generation, token pair management, validation,
and template-based order creation for load testing CoW Protocol.
"""

from .order_factory import OrderFactory
from .order_schema import (
    EIP712Domain,
    OrderBalance,
    OrderKind,
    OrderParameters,
    SignedOrder,
    SigningScheme,
    create_order_hash,
    get_order_domain,
    get_order_types,
)
from .order_templates import (
    OrderTemplate,
    OrderTemplateRegistry,
    create_default_templates,
)
from .order_validation import (
    OrderValidationError,
    assert_valid_order,
    assert_valid_signed_order,
    is_valid_order,
    is_valid_signed_order,
    validate_order_parameters,
    validate_signed_order,
)
from .token_pair import (
    Token,
    TokenPair,
    TokenPairRegistry,
    create_mainnet_token_registry,
    create_polygon_token_registry,
)

__all__ = [
    # Order schema
    "OrderKind",
    "OrderBalance",
    "SigningScheme",
    "OrderParameters",
    "SignedOrder",
    "EIP712Domain",
    "create_order_hash",
    "get_order_domain",
    "get_order_types",
    # Token pairs
    "Token",
    "TokenPair",
    "TokenPairRegistry",
    "create_mainnet_token_registry",
    "create_polygon_token_registry",
    # Order factory
    "OrderFactory",
    # Templates
    "OrderTemplate",
    "OrderTemplateRegistry",
    "create_default_templates",
    # Validation
    "OrderValidationError",
    "validate_order_parameters",
    "validate_signed_order",
    "is_valid_order",
    "is_valid_signed_order",
    "assert_valid_order",
    "assert_valid_signed_order",
]
