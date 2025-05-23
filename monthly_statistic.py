from src.models.db import db
from datetime import datetime

class MonthlyStatistic(db.Model):
    """
    Model for storing monthly ATM/POS/Card statistics
    """
    __tablename__ = 'monthly_statistics'
    
    stat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.bank_id'), nullable=False)
    month = db.Column(db.Date, nullable=False)
    is_revised = db.Column(db.Boolean, default=False)
    
    # ATM and Infrastructure metrics
    atm_onsite = db.Column(db.Integer)
    atm_offsite = db.Column(db.Integer)
    pos_terminals = db.Column(db.Integer)
    micro_atms = db.Column(db.Integer)
    bharat_qr_codes = db.Column(db.Integer)
    upi_qr_codes = db.Column(db.Integer)
    credit_cards = db.Column(db.Integer)
    debit_cards = db.Column(db.Integer)
    
    # Transaction metrics
    pos_txn_volume = db.Column(db.Integer)
    pos_txn_value = db.Column(db.Numeric(20, 2))
    online_txn_volume = db.Column(db.Integer)
    online_txn_value = db.Column(db.Numeric(20, 2))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MonthlyStatistic {self.bank_id} - {self.month}>'
    
    def to_dict(self):
        """
        Convert monthly statistic object to dictionary
        """
        return {
            'stat_id': self.stat_id,
            'bank_id': self.bank_id,
            'month': self.month.strftime('%Y-%m'),
            'is_revised': self.is_revised,
            'atm_onsite': self.atm_onsite,
            'atm_offsite': self.atm_offsite,
            'pos_terminals': self.pos_terminals,
            'micro_atms': self.micro_atms,
            'bharat_qr_codes': self.bharat_qr_codes,
            'upi_qr_codes': self.upi_qr_codes,
            'credit_cards': self.credit_cards,
            'debit_cards': self.debit_cards,
            'pos_txn_volume': self.pos_txn_volume,
            'pos_txn_value': float(self.pos_txn_value) if self.pos_txn_value else None,
            'online_txn_volume': self.online_txn_volume,
            'online_txn_value': float(self.online_txn_value) if self.online_txn_value else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
