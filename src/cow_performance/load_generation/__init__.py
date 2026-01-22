"""
Load generation module for CoW Protocol performance testing.

This module provides order generation, token pair management, validation,
and template-based order creation for load testing CoW Protocol.
"""

from .abi_encoding import (
    decode_good_after_time_data,
    decode_stop_loss_data,
    decode_twap_data,
    encode_good_after_time_data,
    encode_stop_loss_data,
    encode_twap_data,
)
from .conditional_order_factory import ConditionalOrderFactory

# Conditional order imports
from .conditional_order_schema import (
    ConditionalOrder,
    ConditionalOrderParams,
    GoodAfterTimeOrderParameters,
    StopLossOrderParameters,
    TWAPOrderParameters,
)
from .conditional_order_templates import (
    ConditionalOrderTemplate,
    ConditionalOrderTemplateRegistry,
    create_default_conditional_templates,
)
from .handlers import (
    MAINNET_HANDLERS,
    get_composable_cow_address,
    get_handler_address,
    get_supported_chain_ids,
    get_supported_handler_types,
)
from .oracles import (
    MAINNET_ORACLES,
    OracleRegistry,
    get_oracle_address,
    get_supported_oracle_chains,
)
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
    # Conditional orders
    "ConditionalOrder",
    "ConditionalOrderParams",
    "TWAPOrderParameters",
    "StopLossOrderParameters",
    "GoodAfterTimeOrderParameters",
    "ConditionalOrderFactory",
    "ConditionalOrderTemplate",
    "ConditionalOrderTemplateRegistry",
    "create_default_conditional_templates",
    # Handlers
    "get_handler_address",
    "get_composable_cow_address",
    "get_supported_handler_types",
    "get_supported_chain_ids",
    "MAINNET_HANDLERS",
    # Oracles
    "OracleRegistry",
    "get_oracle_address",
    "get_supported_oracle_chains",
    "MAINNET_ORACLES",
    # ABI Encoding
    "encode_twap_data",
    "encode_stop_loss_data",
    "encode_good_after_time_data",
    "decode_twap_data",
    "decode_stop_loss_data",
    "decode_good_after_time_data",
]
