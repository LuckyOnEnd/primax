import os
import sys

from auth.decorator import token_required
from database.connection import key_col

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from validators.keySchema.keyschema import keySchema
from marshmallow import ValidationError
from flask import request,jsonify
from bson import ObjectId


# validations 
api_key_schema=keySchema()

class KeyController:
    @classmethod
    @token_required
    def Postkey(cls, current_user):
        try:
            if request.method != 'POST':
                return jsonify({'message': 'Such method not allowed', 'success': False}), 404
            data = request.json
            
            try:
                validate_data = api_key_schema.load(data)
                print(validate_data)
                existing_doc = key_col.find_one({'user_id': current_user['user_id']})
                print(existing_doc)   
                if existing_doc:
                    key_col.update_one({"user_id": existing_doc['user_id']}, {"$set": data})
                    return jsonify({
                        'message': 'API Key Updated',
                        'data': validate_data,
                        'success': True
                    }), 200
                else:
                    key_col.insert_one(data)
                    return jsonify({
                        'message': 'API Key Added',
                        'data': validate_data,
                        'success': True
                    }), 200

            except ValidationError as error:
                print(f"Validation Error: {error}")
                return jsonify({
                    'message': 'Validation failed',
                    'error': error.messages,
                    'success': False
                }), 400

        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({
                'message': 'Internal server error',
                'error': str(e),
                'success': False
            }), 500


    @classmethod
    @token_required
    def get_single_key(cls, current_user):
        try:
            result = key_col.find_one({'user_id': current_user['user_id']})

            if result:
                result['_id'] = str(result['_id'])
                result['user_id'] = str(result['user_id'])
                return jsonify({'message': 'Data Retrieved', 'result': result, 'success': True}), 200
            else:
                return jsonify({'message': 'No document found', 'success': False}), 404

        except Exception as e:
            return jsonify({'message': 'Internal Server Error', 'error': str(e), 'success': False}), 500
    
    @classmethod
    @token_required
    def UpdateKey(_id, current_user):
        try:
            data = request.json
            if not data:
                return jsonify({'message': 'No data provided for update'}), 400
            if not _id:
                return jsonify({'message': 'Missing _id in query parameters'}), 400
            try:
                object_id = ObjectId(_id)
            except Exception:
                return jsonify({'message': 'Invalid _id format'}), 400
            result = key_col.update_one(
                {"_id": object_id},  
                {"$set": data}      
            )
            if result.matched_count == 0:
                return jsonify({'message': 'No document found with the given _id'}), 404
            return jsonify({
            'message': 'Document updated successfully',
            'matched_count': result.matched_count,
            'modified_count': result.modified_count,
            'success': True
            }), 200
        except Exception as e:
            return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500