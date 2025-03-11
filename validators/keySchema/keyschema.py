from marshmallow import Schema, fields, validates, ValidationError
from enum import Enum

# Marshmallow schema
class keySchema(Schema):
    # Define fields with validation
    api_key = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "API key is required."},
    )
    api_sec = fields.String(
        required=True,
        validate=lambda x: len(x) > 0,
        error_messages={"required": "API secret is required."},
    )
    type = fields.String(required=True, error_messages={"required": "Type is invalid."})
    signal_type = fields.String()

    amount = fields.Float(
        required=True,
        error_messages={"required": "Amount is required.",
                        "invalid": "Amount must be a positive number greater than 500."},
    )

    trading_view_login = fields.String(
    )

    trading_view_password = fields.String(
    )

    trading_view_chart_link = fields.String(
    )

    @validates('type')
    def validate_type(self, key):
        if key not in ['spot', 'future']:
            raise ValidationError('Type is invalid. Must be Spot or Futures.')

    @validates('api_key')
    def validate_api_key(self, key):
        if len(key) != 64:
            raise ValidationError("API key is invalid. It must be exactly 64 characters.")

    @validates('api_sec')
    def validate_api_sec(self, key):
        if len(key) != 64:
            raise ValidationError("API Secret is invalid. It must be exactly 64 characters.")

    @validates('amount')
    def validate_amount(self, value):
        if value < 5:#todo only for testing
            raise ValidationError("Amount must be greater than 5.")

