from datetime import datetime

from flask import request, jsonify
from marshmallow import Schema, fields, validates, ValidationError

from database.connection import logs_col


class ReportSchema(Schema):
    from_date = fields.DateTime(
        required=True,
    )
    to_date = fields.DateTime(
        required=True,
    )


class ReportController:
    @classmethod
    def get_by_date_range(cls):
        try:
            if request.method != 'POST':
                return jsonify(
                    {'message': 'Such method not allowed', 'success': False}
                    ), 405

            data = request.json

            try:
                validate_data = ReportSchema().load(data)

                result = list(
                    logs_col.find(
                        {
                            "PositionOpened": {
                                "$gte": validate_data['from_date'],
                                "$lte": validate_data['to_date']
                            }
                        }
                    )
                )

                total_loss = 0
                total_profit = 0
                total_commission = 0
                net_profit = 0

                for order in result:
                    realized_pnl = float(order.get('realized_pnl', 0))
                    commission = float(order.get('commission', 0))

                    if realized_pnl < 0:
                        total_loss += abs(
                            realized_pnl
                        )
                    else:
                        total_profit += realized_pnl

                    total_commission += abs(commission)
                    net_profit = total_profit - total_loss - total_commission

                total_loss = round(-total_loss, 5)
                total_profit = round(total_profit, 5)
                total_commission = round(-total_commission, 5)
                net_profit = round(net_profit, 5)

                return jsonify(
                    {
                        'message': 'Success',
                        'data': {
                            "total_loss": total_loss,
                            "total_profit": total_profit,
                            "total_commission": total_commission,
                            "net_profit": net_profit
                        },
                        'success': True
                    }
                ), 200
            except ValidationError as error:
                return jsonify(
                    {
                        'message': 'Validation error',
                        'error': error.messages,
                        'success': False
                    }
                ), 400

        except Exception as ex:
            print(ex)
