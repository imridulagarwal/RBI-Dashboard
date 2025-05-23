from src.models.db import db

class Bank(db.Model):
    """
    Model for storing bank information
    """
    __tablename__ = 'banks'
    
    bank_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bank_name = db.Column(db.String(255), nullable=False)
    bank_type = db.Column(db.String(50), nullable=False)  # 'Scheduled Commercial', 'Public Sector', 'Private Sector'
    
    # Relationship with monthly statistics
    statistics = db.relationship('MonthlyStatistic', backref='bank', lazy=True)
    
    def __repr__(self):
        return f'<Bank {self.bank_name}>'
    
    def to_dict(self):
        """
        Convert bank object to dictionary
        """
        return {
            'bank_id': self.bank_id,
            'bank_name': self.bank_name,
            'bank_type': self.bank_type
        }
