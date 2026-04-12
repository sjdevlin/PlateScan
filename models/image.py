from sqlalchemy import Column, Float, Integer, String

from .base import Base


class ImageSet(Base):
    __tablename__ = "ImageSet"

    id = Column(Integer, primary_key=True)
    description = Column(String)
    wells = Column(String)
    number_of_sites = Column(Integer)
    stack_size = Column(Integer)
    stack_step_size = Column(Integer)
    channel_1_number = Column(Integer)
    channel_1_intensity = Column(Float)
    channel_2_number = Column(Integer)
    channel_2_intensity = Column(Float)
