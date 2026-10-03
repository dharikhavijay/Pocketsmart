from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RecommendationHistory(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category = Column(String(50), nullable=False)  # 'home', 'party', 'jewelry'
    title = Column(String(255), nullable=False)
    total_budget = Column(Float, nullable=False)
    input_parameters = Column(Text, nullable=False)  # JSON string of input options
    image_path = Column(String(500), nullable=True)   # Relative path to uploaded outfit image
    ai_response_json = Column(Text, nullable=False)  # JSON string of parsed recommendations
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recommendations")

    def __repr__(self):
        return f"<RecommendationHistory id={self.id} category='{self.category}' budget={self.total_budget}>"


class Testimonial(Base):
    __tablename__ = "testimonials"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False)
    role_or_occasion = Column(String(100), nullable=False)
    comment = Column(Text, nullable=False)
    rating = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Testimonial id={self.id} user='{self.user_name}'>"
