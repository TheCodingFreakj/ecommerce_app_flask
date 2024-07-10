from datetime import datetime
from . import db
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)  # Version column for optimistic concurrency control

