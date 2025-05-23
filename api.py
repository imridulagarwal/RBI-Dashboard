from flask import Blueprint, jsonify, request
from src.models.bank import Bank
from src.models.monthly_statistic import MonthlyStatistic
from src.models.db import db
from datetime import datetime
import calendar

api_bp = Blueprint('api', __name__)

@api_bp.route('/banks', methods=['GET'])
def get_banks():
    """Get all banks or filter by bank type"""
    bank_type = request.args.get('bank_type')
    
    if bank_type:
        banks = Bank.query.filter_by(bank_type=bank_type).all()
    else:
        banks = Bank.query.all()
    
    return jsonify({
        'success': True,
        'count': len(banks),
        'data': [bank.to_dict() for bank in banks]
    })

@api_bp.route('/bank-types', methods=['GET'])
def get_bank_types():
    """Get distinct bank types"""
    bank_types = db.session.query(Bank.bank_type).distinct().all()
    return jsonify({
        'success': True,
        'data': [bank_type[0] for bank_type in bank_types]
    })

@api_bp.route('/months', methods=['GET'])
def get_months():
    """Get available months in the database"""
    months = db.session.query(MonthlyStatistic.month).distinct().order_by(MonthlyStatistic.month.desc()).all()
    return jsonify({
        'success': True,
        'data': [month[0].strftime('%Y-%m') for month in months]
    })

@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get statistics with optional filters"""
    # Parse query parameters
    month = request.args.get('month')
    bank_id = request.args.get('bank_id')
    bank_type = request.args.get('bank_type')
    metric = request.args.get('metric')
    
    # Start with base query
    query = db.session.query(MonthlyStatistic).join(Bank)
    
    # Apply filters
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            start_date = datetime(year, month_num, 1)
            last_day = calendar.monthrange(year, month_num)[1]
            end_date = datetime(year, month_num, last_day)
            query = query.filter(MonthlyStatistic.month.between(start_date, end_date))
        except (ValueError, IndexError):
            return jsonify({'success': False, 'error': 'Invalid month format. Use YYYY-MM'}), 400
    
    if bank_id:
        try:
            query = query.filter(MonthlyStatistic.bank_id == int(bank_id))
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid bank_id'}), 400
    
    if bank_type:
        query = query.filter(Bank.bank_type == bank_type)
    
    # Execute query
    statistics = query.all()
    
    # Filter by metric if specified
    if metric and statistics:
        result = []
        for stat in statistics:
            stat_dict = stat.to_dict()
            if metric in stat_dict:
                result.append({
                    'bank_id': stat_dict['bank_id'],
                    'bank_name': Bank.query.get(stat_dict['bank_id']).bank_name,
                    'month': stat_dict['month'],
                    metric: stat_dict[metric]
                })
        return jsonify({
            'success': True,
            'count': len(result),
            'data': result
        })
    
    # Return all data if no metric specified
    return jsonify({
        'success': True,
        'count': len(statistics),
        'data': [stat.to_dict() for stat in statistics]
    })

@api_bp.route('/analytics/growth', methods=['GET'])
def get_growth_analytics():
    """Calculate month-on-month growth for a specific metric"""
    # Parse query parameters
    metric = request.args.get('metric')
    bank_id = request.args.get('bank_id')
    bank_type = request.args.get('bank_type')
    start_month = request.args.get('start_month')
    end_month = request.args.get('end_month')
    
    if not metric:
        return jsonify({'success': False, 'error': 'Metric parameter is required'}), 400
    
    # Start with base query
    query = db.session.query(MonthlyStatistic, Bank.bank_name).join(Bank)
    
    # Apply filters
    if bank_id:
        try:
            query = query.filter(MonthlyStatistic.bank_id == int(bank_id))
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid bank_id'}), 400
    
    if bank_type:
        query = query.filter(Bank.bank_type == bank_type)
    
    if start_month:
        try:
            year, month_num = map(int, start_month.split('-'))
            start_date = datetime(year, month_num, 1)
            query = query.filter(MonthlyStatistic.month >= start_date)
        except (ValueError, IndexError):
            return jsonify({'success': False, 'error': 'Invalid start_month format. Use YYYY-MM'}), 400
    
    if end_month:
        try:
            year, month_num = map(int, end_month.split('-'))
            last_day = calendar.monthrange(year, month_num)[1]
            end_date = datetime(year, month_num, last_day)
            query = query.filter(MonthlyStatistic.month <= end_date)
        except (ValueError, IndexError):
            return jsonify({'success': False, 'error': 'Invalid end_month format. Use YYYY-MM'}), 400
    
    # Order by bank and month
    query = query.order_by(MonthlyStatistic.bank_id, MonthlyStatistic.month)
    
    # Execute query
    results = query.all()
    
    # Calculate growth
    growth_data = {}
    for i in range(1, len(results)):
        current = results[i][0]
        previous = results[i-1][0]
        
        # Skip if not the same bank
        if current.bank_id != previous.bank_id:
            continue
        
        # Get metric values
        current_value = getattr(current, metric, 0) or 0
        previous_value = getattr(previous, metric, 0) or 0
        
        # Calculate growth percentage
        growth_pct = 0
        if previous_value > 0:
            growth_pct = ((current_value - previous_value) / previous_value) * 100
        
        # Format month
        month_str = current.month.strftime('%Y-%m')
        
        # Add to growth data
        if current.bank_id not in growth_data:
            growth_data[current.bank_id] = {
                'bank_name': results[i][1],
                'growth': []
            }
        
        growth_data[current.bank_id]['growth'].append({
            'month': month_str,
            'value': current_value,
            'previous_value': previous_value,
            'growth_percentage': round(growth_pct, 2)
        })
    
    return jsonify({
        'success': True,
        'metric': metric,
        'data': growth_data
    })

@api_bp.route('/analytics/comparison', methods=['GET'])
def get_comparison_analytics():
    """Compare metrics across banks"""
    # Parse query parameters
    metric = request.args.get('metric')
    bank_ids = request.args.get('bank_ids')
    month = request.args.get('month')
    
    if not metric:
        return jsonify({'success': False, 'error': 'Metric parameter is required'}), 400
    
    if not bank_ids:
        return jsonify({'success': False, 'error': 'bank_ids parameter is required'}), 400
    
    try:
        bank_id_list = [int(id.strip()) for id in bank_ids.split(',')]
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid bank_ids format. Use comma-separated integers'}), 400
    
    # Start with base query
    query = db.session.query(MonthlyStatistic, Bank.bank_name).join(Bank)
    
    # Filter by bank IDs
    query = query.filter(MonthlyStatistic.bank_id.in_(bank_id_list))
    
    # Filter by month if specified
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            start_date = datetime(year, month_num, 1)
            last_day = calendar.monthrange(year, month_num)[1]
            end_date = datetime(year, month_num, last_day)
            query = query.filter(MonthlyStatistic.month.between(start_date, end_date))
        except (ValueError, IndexError):
            return jsonify({'success': False, 'error': 'Invalid month format. Use YYYY-MM'}), 400
    
    # Order by month and bank
    query = query.order_by(MonthlyStatistic.month, MonthlyStatistic.bank_id)
    
    # Execute query
    results = query.all()
    
    # Organize comparison data
    comparison_data = {}
    for stat, bank_name in results:
        month_str = stat.month.strftime('%Y-%m')
        
        if month_str not in comparison_data:
            comparison_data[month_str] = []
        
        # Get metric value
        metric_value = getattr(stat, metric, 0) or 0
        
        comparison_data[month_str].append({
            'bank_id': stat.bank_id,
            'bank_name': bank_name,
            'value': metric_value
        })
    
    return jsonify({
        'success': True,
        'metric': metric,
        'data': comparison_data
    })
