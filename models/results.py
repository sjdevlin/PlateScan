from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class ResultRun(Base):
    __tablename__ = "ResultRun"

    id = Column(Integer, primary_key=True)
    plate_id = Column(Integer, ForeignKey("Plate.id"), nullable=False)
    image_set_id = Column(Integer, ForeignKey("ImageSet.id"), nullable=False)
    description = Column(String)
    start_date_time = Column(DateTime)
    finish_date_time = Column(DateTime)
    status = Column(String)

    image = relationship(
        "Image",
        backref="parent",
        cascade="all, delete-orphan",
        single_parent=True,
    )


class Image(Base):
    __tablename__ = "Image"

    id = Column(Integer, primary_key=True)
    result_run_id = Column(Integer, ForeignKey("ResultRun.id"), nullable=False)
    well_row = Column(String)
    well_column = Column(Integer)
    site_number = Column(Integer)
    stack_number = Column(Integer)
    led_number = Column(Integer)
    dimension_x = Column(Integer)
    dimension_y = Column(Integer)
    file_path = Column(String)
    timestamp = Column(DateTime)
    focus_score = Column(Float)
